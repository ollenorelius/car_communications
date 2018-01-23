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

class CarController:
    context = zmq.Context()

    lidar_socket = context.socket(zmq.SUB)
    image_socket = context.socket(zmq.SUB)
    command_socket = context.socket(zmq.REQ)
    outbound_queue = Queue()
    image_stream = io.BytesIO()
    RC_connection_lock = threading.RLock()
    message_lock = threading.RLock()


    pr = ProtocolReader()


    def __init__(self, address='autopi.local', port=8000):

        self.lidar_socket.setsockopt(zmq.RCVHWM, 1)
        self.image_socket.setsockopt(zmq.RCVHWM, 1)
        self.command_socket.setsockopt(zmq.RCVHWM, 1)
        self.command_socket.setsockopt(zmq.SNDHWM, 1)
        lidar_filter = "lidar"

        self.lidar_socket.setsockopt_string(zmq.SUBSCRIBE, lidar_filter)
        self.image_socket.setsockopt(zmq.SUBSCRIBE, b"image")

        self.lidar_socket.connect("tcp://autonomous-platform.local:5556")
        self.image_socket.connect("tcp://autonomous-platform.local:5556")
        self.command_socket.connect("tcp://autonomous-platform.local:5555")

        self.data = {"camera": self.get_picture,
                "lidar": self.get_lidar,
                "speed": self.get_speed}
        print("Car controller init OK!")
        threading.Thread(target=self.heartbeat_thread, daemon=True).start()
        threading.Thread(target=self.flush_messages, daemon=True).start()


    def get_picture(self, camera_id=0):

        img_bytes = self.image_socket.recv()[6:]
        try:
            temp_image = Image.open(io.BytesIO(img_bytes))
        except OSError:
            print("Received invalid image! Len: len(%s)" % len(img_bytes))
            return None
        return temp_image

    def get_lidar(self, lidarID=0):
        string = self.lidar_socket.recv()
        data = [int(x) for x in string.split()[1:]]
        print(data)
        data = np.reshape(data, (-1, 3))
        return data

    def get_speed(self):
        pass

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
