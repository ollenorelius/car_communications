"""Ground station car control object."""

import socket
import threading
import time
import io
import struct
import comms_bytes as cb
from protocol_reader import ProtocolReader
from PIL import Image, ImageQt, ImageDraw, ImageFont, ImageOps

class CarController:
    RC_socket = socket.socket()
    image_stream = io.BytesIO
    RC_connection_lock = threading.Lock()
    pr = ProtocolReader()

    def __init__(self, address='autopi.local', port=8000):
        self.RC_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.RC_socket.settimeout(2)
        self.RC_socket.connect((address, port))
        self.RC_connection = self.RC_socket.makefile('rwb')
        #threading.Thread(target=self.heartbeat_thread, daemon=True).start()

    def get_picture(self, id):
        print("sending pic rq")
        reply = self.send_message(cb.REQ_SENS, cb.REQ_PIC)
        print("got reply: " + str(reply))
        if int.from_bytes(reply[0], 'big') == cb.R_OK:
            print("receiving picture!")
            dataL = struct.unpack('<L', reply[1:])[0]
            self.RC_connection.read(dataL)
            self.image_stream.seek(0)
            self.image_stream.write(self.RC_connection.read(dataL))
            # Rewind the stream, open it as an image with PIL and do some
            # processing on it
            self.image_stream.seek(0)
            temp_image = Image.open(self.image_stream) \
                .transpose(Image.FLIP_TOP_BOTTOM) \
                .transpose(Image.FLIP_LEFT_RIGHT)
            return temp_image

    def send_message(self, group, command, data=[]):
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
        with self.RC_connection_lock:
            self.RC_connection.write(struct.pack('<B', cb.START))
            self.RC_connection.write(struct.pack('<B', group))
            self.RC_connection.write(struct.pack('<B', command))
            if data != []:
                print(data)
                self.RC_connection.write(data)
            self.RC_connection.write(struct.pack('<B', cb.END))
            self.RC_connection.flush()
            reply = self.recv_message()
            print("reply in send_message: " + str(reply))
            return reply

    def recv_message(self):
        """Read an incoming message from Raspberry Pi."""
        timedout = False
        print("boop")
        while not self.pr.messageInBuffer:
            ser_byte = self.RC_connection.read(1)
            self.pr.readByte(ser_byte)
            if ser_byte == b'':
                timedout = True
        if not timedout:
            return self.pr.buf
        else:
            return False

    def set_speed(self, speed):
        self.send_message(cb.CMD_SPEED, cb.CAR_SPD, struct.pack('<b', speed))

    def set_turnrate(self, rate):
        self.send_message(cb.CMD_SPEED, cb.TURN_SPD, struct.pack('<b', rate))

    def heartbeat_thread(self):
        """Thread method for sending regular heartbeat."""
        while True:
            reply = self.send_message(group=cb.CMD_STATUS,
                                      command=cb.HEARTBEAT)
            time.sleep(0.5)
