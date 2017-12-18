"""Connection handler for Infotiv Autonomous car platform."""

import serial
import server.comms_bytes as cb
import threading
import time
from server.protocol_reader import ProtocolReader
import struct

class CarSerial:
    """Connection handler for Infotiv Autonomous car platform."""

    connection = 0
    connection_lock = threading.RLock()
    pr = ProtocolReader()

    def __init__(self, serial_port='/dev/ttyAMA0', baudrate=115200):
        """
        Constructor for the CarConnection.

        serial_port:
            serial_port is the connection string for the arduino serial. On
            linux systems it's typically /dev/ttyAMA0 or /dev/ttyACM0.
            In specific cases it may be /dev/ttyS0 on a Raspberry Pi,
            if hardware serial has been configured that way. If you are
            running this code on Windows, it's COM[something] with no brackets.

        baudrate:
            Integer value of bits per second. Default is 115,200 though other
            common ones are 9,600 and 250,000.
        """
        # Initialize  serial to Arduino
        self.connection = serial.Serial(port=serial_port,
                                        baudrate=baudrate,
                                        timeout=0.2)
        # start heartbeat thread
        threading.Thread(target=self.heartbeat_thread,
                         args=(),
                         daemon=True).start()

    def send_message(self, group, command=0x01, data=[]):
        """
        Send a message to the Arduino.

        group:
            A byte representing command group.
            See comms_bytes.py for reference.
        command:
            A byte representing command within group.
            See comms_bytes.py for reference.
        data:
            byte array containing data related to command being sent.

        Returns the reply received from the arduino as a byte array.
        """
        with self.connection_lock:
            self.connection.write([cb.START])
            self.connection.write(struct.pack('>L', 2+len(data)))
            self.connection.write([group])
            self.connection.write([command])
            # print("in send_message, command = %s:" % str(command))
            if data != []:
                print("in send_message, data = %s:" % str(data))
                self.connection.write([d for d in data])
            self.connection.write([cb.END])
            reply = self.recv_message()
            return reply

    def recv_message(self):
        """Read an incoming message from Arduino."""
        timedout = False
        while not self.pr.message_in_buffer:
            ser_byte = self.connection.read(self.pr.next_symbol_length)
            if ser_byte != b'':
                print(ser_byte)
            self.pr.readBytes(ser_byte)
            if ser_byte == b'':
                timedout = True
            print(self.pr.buf)
        if not timedout:
            return self.pr.buf
        else:
            return False

    def heartbeat_thread(self):
        """Thread method for sending regular heartbeat."""
        while True:
            reply = self.send_message(group=cb.CMD_STATUS,
                                      command=cb.HEARTBEAT)
            time.sleep(0.5)
