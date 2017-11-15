"""Ground station car control object."""

import socket
import threading
import time
import io
import struct
import autonomous.comms_bytes as cb
from autonomous.protocol_reader import ProtocolReader
from PIL import Image, ImageQt, ImageDraw, ImageFont, ImageOps

class CarController:
    RC_socket = socket.socket()
    image_stream = io.BytesIO()
    RC_connection_lock = threading.RLock()
    message_lock = threading.RLock()

    pr = ProtocolReader()


    def __init__(self, address='autopi.local', port=8000):
        self.RC_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.RC_socket.settimeout(100)
        self.RC_socket.connect((address, port))
        self.RC_connection = self.RC_socket.makefile('rwb')
        threading.Thread(target=self.heartbeat_thread, daemon=True).start()

    def get_picture(self, camera_id):
        with self.message_lock:
            print("sending pic rq")
            reply = self.send_message(cb.REQ_SENS,
                                      cb.REQ_PIC,
                                      struct.pack('>B', camera_id))
            print("get_picture got reply: " + str(reply))
            if reply[0] == cb.R_OK_IMAGE_FOLLOWS:
                print("receiving picture!")
                print(reply)
                dataL = struct.unpack('>L', reply[2:6])[0]
                print("picture size: %s bytes" % dataL)
                if dataL > 0:
                    self.image_stream.seek(0)
                    with self.RC_connection_lock:
                        while not self.pr.message_in_buffer:
                            self.pr.readByte(self.RC_connection.read(1))
                        self.image_stream.write(self.pr.buf)
                        self.pr.message_in_buffer = False
                        #self.image_stream.write(self.RC_connection.read(dataL+2))
                    # Rewind the stream, open it as an image with PIL and do some
                    # processing on it
                    self.image_stream.seek(0)
                    #print("escaped picture is %s" % len(self.image_stream))
                    img_bytes = self.unescape_buffer(self.image_stream.getvalue()[2:])
                    print("deescaped picture is %s" % len(img_bytes))
                    try:
                        temp_image = Image.open(io.BytesIO(img_bytes))
                    except OSError:
                        print("Received invalid image! Len: len(%s)" % len(img_bytes))
                        return None
                    return temp_image
                else:
                    return None

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
        with self.message_lock:
            with self.RC_connection_lock:
                self.RC_connection.write(struct.pack('>B', cb.START))
                self.RC_connection.write(struct.pack('>L', 2+len(data)))
                self.RC_connection.write(struct.pack('>B', group))
                self.RC_connection.write(struct.pack('>B', command))
                if data != []:
                    print(data)
                    self.RC_connection.write(data)
                self.RC_connection.write(struct.pack('>B', cb.END))
                self.RC_connection.flush()
            reply = self.recv_message()
        print("reply in send_message: " + str(reply))
        return reply

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
        print("recv_message got %s" % self.pr.buf)
        if not timedout:
            self.pr.message_in_buffer = False
            return self.pr.buf
        else:
            self.pr.message_in_buffer = False
            return False

    def set_speed(self, speed):
        self.send_message(cb.CMD_SPEED, cb.CAR_SPD, struct.pack('>b', speed))

    def set_turnrate(self, rate):
        self.send_message(cb.CMD_SPEED, cb.TURN_SPD, struct.pack('>b', rate))

    def heartbeat_thread(self):
        """Thread method for sending regular heartbeat."""
        while True:
            reply = self.send_message(group=cb.CMD_STATUS,
                                      command=cb.HEARTBEAT)
            time.sleep(0.5)
