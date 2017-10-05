"""Connection handler for Infotiv Autonomous car platform."""

import serial
import comms_bytes as cb
import threading
import time


class CarConnection:
    """Connection handler for Infotiv Autonomous car platform."""

    connection = 0
    connection_lock = threading.Lock()

    def __init__(self, serial_port='/dev/ttyAMA0', baudrate=115200):
        self.connection = serial.Serial(serial_port, baudrate)
        # Initialize  serial to Arduino
        threading.Thread(target=self.heartbeat_thread,
                         args=(),
                         daemon=True).start()

        threading.Thread(target=self.debug_thread,
                         args=(),
                         daemon=True).start()
        # start heartbeat thread

    def send_message(self, group, command=0x01, data=[]):
        with self.connection_lock:
            self.connection.write([cb.START])
            self.connection.write([group])
            self.connection.write([command])
            if data != []:
                print(data)
                self.connection.write(data)
            self.connection.write([cb.END])

    def heartbeat_thread(self):
        while True:
            self.send_message(group=cb.CMD_STATUS, command=cb.HEARTBEAT)
            time.sleep(0.5)

    def debug_thread(self):
        while True:
            b = self.connection.in_waiting
            print(self.connection.read(b))
            time.sleep(0.5)
