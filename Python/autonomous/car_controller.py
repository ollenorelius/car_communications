"""Ground station car control object."""

import socket
import threading
import time
import io
import struct
import common.comms_bytes as cb
import common.message as msg
from autonomous.protocol_reader import ProtocolReader
from PIL import Image, ImageQt, ImageDraw, ImageFont, ImageOps
import zmq
from queue import Queue
import numpy as np

def conf_sub(socket, filter_bytes, address):
    socket.setsockopt(zmq.RCVHWM, 1)
    socket.setsockopt(zmq.RCVTIMEO, 1000)
    socket.setsockopt(zmq.SUBSCRIBE, filter_bytes)
    socket.connect(address)

class CarController:

    outbound_queue = Queue()
    image_stream = io.BytesIO()
    RC_connection_lock = threading.RLock()
    message_lock = threading.RLock()


    pr = ProtocolReader()


    def __init__(self, address='192.168.150.133', context = None):
        self.context = context
        if context is None:
            self.context = zmq.Context()

        self.lidar_socket = self.context.socket(zmq.SUB)
        self.sonar_socket = self.context.socket(zmq.SUB)
        self.speed_socket = self.context.socket(zmq.SUB)
        self.image_socket = self.context.socket(zmq.SUB)
        self.battery_socket = self.context.socket(zmq.SUB)
        self.ltst_cmd_socket = self.context.socket(zmq.SUB)
        self.compass_socket = self.context.socket(zmq.SUB)

        self.command_socket = self.context.socket(zmq.REQ)

        cmd_address = "tcp://"+address+":5555"
        data_address = "tcp://"+address+":5556"
        conf_sub(self.lidar_socket, bytes([cb.SENS, cb.SENS_LIDAR]), data_address)
        conf_sub(self.image_socket, bytes([cb.SENS, cb.SENS_PIC]), data_address)
        conf_sub(self.speed_socket, bytes([cb.SENS, cb.SENS_WHEEL]), data_address)
        conf_sub(self.battery_socket, bytes([cb.SENS, cb.SENS_P_BATT]), data_address)
        conf_sub(self.ltst_cmd_socket, bytes([cb.CMD_STATUS, cb.LATEST_CMD]), data_address)
        conf_sub(self.sonar_socket, bytes([cb.SENS, cb.SENS_SONAR]), data_address)
        conf_sub(self.compass_socket, bytes([cb.SENS, cb.SENS_COMPASS]), data_address)

        self.command_socket.setsockopt(zmq.RCVHWM, 1)
        self.command_socket.setsockopt(zmq.SNDHWM, 1)

        self.command_socket.connect(cmd_address)

        self.data = {"camera": self.get_picture,
                "lidar": self.get_lidar,
                "wheel_speed": self.get_wheel_speeds}
        threading.Thread(target=self.heartbeat_thread, daemon=True).start()
        threading.Thread(target=self.flush_messages, daemon=True).start()
        print("Car controller init OK!")

     
    def _get_data_from_socket(self, socket):
        """
        * Retreives the data from a message. 
        * @param The socket to receive from
        * @return The data portion of a Message. The data portion is usually another Message object.
        """
        try:
            string = socket.recv()[4:] 
            return string
        except zmq.error.Again:
            print("Timeout receiving data from socket")
            return None


    def get_picture(self, camera_id=0):
        img_bytes = self._get_data_from_socket(self.image_socket)
        try:
            temp_image = Image.open(io.BytesIO(img_bytes))
        except OSError:
            if img_bytes is not None:
                print("Received invalid image! Len: len(%s)" % len(img_bytes))
            else:
                print("Received None image")
            return None
        return temp_image

    def get_lidar(self, lidarID=0):
        string = self._get_data_from_socket(self.lidar_socket)
        if string is not None:
            points = map(self.decode_lidar_chunk, self.lidar_chunks(string))
            data = np.array(list(points))*[1, 1/4, 1/64*np.pi/180]
            return data
        else:
            return None

    def decode_lidar_chunk(self, chunk):
        """Map a chunk of lidar data into (quality, distance, angle)."""
        #print("decoding chunk: %s" % chunk)
        print(chunk)
        return struct.unpack(">BHH", chunk)

    def lidar_chunks(self, data):
        """Generator for getting lidar data one point at a time."""
        lidar_chunk_size = 5
        for i in range(0, len(data), lidar_chunk_size):
            yield data[i:i + lidar_chunk_size]

    def get_wheel_speeds(self):
        string = self._get_data_from_socket(self.speed_socket)
        if string is not None:
            string = self.pr.unescape_buffer(string)
            return struct.unpack(">hhhh", string[:8])
        else:
            return None

    def get_sonar(self, id):
        sonar_string = self._get_data_from_socket(self.sonar_socket)
        if sonar_string is not None and sonar_string != b'':
            sonar_string = self.pr.unescape_buffer(sonar_string)
            data = struct.unpack(">hB", sonar_string[:3])
            if data[1] == id:
                return data[0]
            else:
                return None
        else:
            return None

    def get_voltage(self):
        string = self._get_data_from_socket(self.battery_socket)
        if string is not None:
            string = self.pr.unescape_buffer(string)
            v = struct.unpack(">hh", string[:4])[0]
            return v
        else:
            return None

    def get_current(self):
        string = self._get_data_from_socket(self.battery_socket)
        if string is not None:
            string = self.pr.unescape_buffer(string)
            i = struct.unpack(">hh", string[:4])[1]
            return i
        else:
            return None

    def get_latest_cmd(self):
        cmd_content = self._get_data_from_socket(self.ltst_cmd_socket)
        if cmd_content is not None:
            return cmd_content
        else:
            return None

    def get_compass(self):
        heading_raw = self._get_data_from_socket(self.compass_socket)
        if heading_raw is not b'' and heading_raw is not None:
            heading = struct.unpack(">h", heading_raw[0:2])
            return heading

    def flush_messages(self):
        while True:
            self.command_socket.send(self.outbound_queue.get().get_zmq_msg())
            reply = msg.Message(self.command_socket.recv())

    def send_message(self, message):
        """
        Send a message to the Raspberry Pi.

        group:
            A byte representing command group.
            See comms_bytes.py for reference.
        command:
            A byte representing command within group.
            See comms_bytes.py for reference.
        data:
            byte array containing data related to command being sent.

        Returns the reply received from the Raspberry Pi as a byte array.
        """
        self.outbound_queue.put(message)

    def recv_message(self):
        """Read an incoming message from Raspberry Pi."""
        timedout = False
        print("receiving message... ", end="")
        with self.RC_connection_lock:
            while not self.pr.message_in_buffer:
                ser_byte = self.RC_connection.read(self.pr.next_symbol_length)
                self.pr.readBytes(ser_byte)
                if ser_byte == b'':
                    timedout = True
                    print("timeout!")
        #print("recv_message got %s" % self.pr.get_buffer())
        if not timedout:
            print("got message.")
            self.pr.message_in_buffer = False
            return self.pr.get_buffer()
        else:
            self.pr.message_in_buffer = False
            return False

    def arm_motors(self):
        self.send_message(message=msg.ArmMotorsMessage())

    def disarm_motors(self):
        self.send_message(message=msg.DisarmMotorsMessage())

    def set_speed(self, speed):
        self.send_message(message=msg.SetSpeed(speed))
        # print(struct.pack('>h', speed))

    def set_turnrate(self, rate):
        self.send_message(message=msg.SetTurnRate(rate))

    def heartbeat_thread(self):
        """Thread method for sending regular heartbeat."""
        while True:
            reply = self.send_message(msg.Heartbeat())
            time.sleep(0.5)
