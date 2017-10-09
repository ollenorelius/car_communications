#!/usr/bin/python3
"""Server application running in the background on the Raspberry Pi."""
import socket
import io
import picamera
import struct
import time
import threading
from car_serial import CarSerial
from protocol_reader import ProtocolReader
import comms_bytes as cb


inbound_socket = socket.socket()
inbound_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
inbound_socket.bind(('0.0.0.0', 8000))
inbound_socket.listen(0)

camera = picamera.PiCamera()
camera.resolution = (320, 240)
camera.sensor_mode = 7
camera.shutter_speed = 10000
camera.framerate = 40
camera.rotation = 180

car = CarSerial()

timing = False
image_lock = threading.Lock()

image = b'asdf'


def time_op(start, name):
    """Timing function used for debug."""
    tt = time.time() - start
    if timing:
        print('Time taken for %s: %s' % (name, tt))
    return time.time()


def camera_thread():
    """Thread for capturing camera image asynchronously."""
    global image
    cam_stream = io.BytesIO()
    for foo in camera.capture_continuous(output=cam_stream,
                                         format='jpeg',
                                         use_video_port=True,
                                         quality=15,
                                         thumbnail=None):
        cam_stream.seek(0)
        image = cam_stream.read()
        cam_stream.seek(0)
        cam_stream.truncate()

        # if no clients are connected, just chill ad wait to save power.
        while(threading.active_count() < 3):
            time.sleep(0.2)


def network_thread(inbound_socket):
    """Client handler thread."""
    client_connection = inbound_socket.makefile('rwb')
    # buf = bytearray([0])
    global image
    pr = ProtocolReader()
    ch = CommandHandler(car)
    while True:
        while not pr.messageInBuffer:
            inputByte = client_connection.read(1)
            if inputByte == b'':
                return 0
            pr.readByte(inputByte)
            print(inputByte)
            print(pr.messageInBuffer)
        print("Got full message!")
        ch.readBuffer(pr.buf, client_connection)
        pr.messageInBuffer = False


class CommandHandler:
    """Parses commands from the buffer in ProtocolReader."""

    car = []

    def __init__(self, car):
        """Constructor. Pass the car object to be controlled."""
        self.car = car

    def checksum(self, buf):
        """Create a simple checksum by XORing all the bytes in the message."""
        chksum = 0
        for byte in buf:
            chksum ^= int.from_bytes(byte, 'big')
        return chksum

    def sendOK(self, buf, conn, data=[]):
        """
        Send an OK response.

        buf:
            buffer containing message data.
        conn:
            connection to send response over.
        data:
            byte array to append to message.
        """
        print("Sending OK: " + str(self.checksum(buf)) + " data: " + str(data))
        conn.write(bytes(cb.START))
        conn.write(bytes(cb.R_OK))
        conn.write(bytes(self.checksum(buf)))
        for datum in data:
            conn.write(bytes(datum))
        conn.write(bytes(cb.END))
        conn.flush()
        return 1

    def readBuffer(self, buf, conn):
        group = int.from_bytes(buf[0], 'big')
        command = int.from_bytes(buf[1], 'big')
        data = buf[2:]
        print("got: " + str(buf))
        # Use these to override functionality if desired.
        if group == cb.CMD_STATUS:
            if command == cb.HEARTBEAT:
                pass
            elif command == cb.HANDSHAKE:
                pass
            elif command == cb.ASK_STATUS:
                pass

        elif group == cb.CMD_SPEED:
            if command == cb.WHEEL_SPD:
                pass
            elif command == cb.CAR_SPD:
                pass
            elif command == cb.TURN_SPD:
                pass

        elif group == cb.CMD_SPEED_CL:
            if command == cb.DIST_CL:
                pass
            elif command == cb.TURN_CL:
                pass
            elif command == cb.TURN_ABS_CL:
                pass

        elif group == cb.REQ_SENS:
            if command == cb.REQ_COMPASS:
                pass
            elif command == cb.REQ_ACC:
                pass
            elif command == cb.REQ_GYRO:
                pass
            elif command == cb.REQ_PIC:
                print('Got picture request!')
                global image
                self.sendOK(buf, conn, [struct.pack('<L', len(image))])
                with image_lock:
                    conn.write(image)
                conn.flush()
                return 1

        car.send_message(group=group, command=command, data=data)
        self.sendOK(buf, conn)


threading.Thread(target=camera_thread, daemon=True).start()
while True:
    connection, addr = inbound_socket.accept()
    threading.Thread(target=network_thread, args=[connection]).start()
    print(connection)
