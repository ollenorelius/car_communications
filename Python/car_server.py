#!/usr/bin/python3

import socket
import io
import picamera
import sys
import struct
import time
import threading
from car_connection import CarConnection
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

car = CarConnection()

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

    while True:
        t = time.time()
        command = client_connection.read(1)
        fwd = int(100)
        bck = int(130)
        rgt = int(130)
        lft = int(120)
        if command != b'':
            t = time_op(t, 'recv command')
            if command == b'p':
                t = time.time()
                with image_lock:
                    t = time_op(t, 'capture')
                    client_connection.write(struct.pack('<L', len(image)))
                    t = time_op(t, 'send header')
                    # Rewind the stream and send the image data over the wire
                    client_connection.write(image)
                client_connection.flush()
                t = time_op(t, 'send data')
            elif command == b'w':
                car.send_message(cb.CMD_SPEED, command=cb.CAR_SPD, data=[fwd])
            elif command == b'W':
                car.send_message(cb.CMD_SPEED, command=cb.CAR_SPD, data=[0])
            elif command == b's':
                car.send_message(cb.CMD_SPEED, command=cb.CAR_SPD, data=[bck])
            elif command == b'S':
                car.send_message(cb.CMD_SPEED, command=cb.CAR_SPD, data=[0])
            elif command == b'a':
                car.send_message(cb.CMD_SPEED, command=cb.TURN_SPD, data=[lft])
            elif command == b'A':
                car.send_message(cb.CMD_SPEED, command=cb.TURN_SPD, data=[0])
            elif command == b'd':
                car.send_message(cb.CMD_SPEED, command=cb.TURN_SPD, data=[rgt])
            elif command == b'D':
                car.send_message(cb.CMD_SPEED, command=cb.TURN_SPD, data=[0])
        else:
            raise Exception('Stream broken!')

threading.Thread(target=camera_thread, daemon=True).start()
while True:
    connection, addr = inbound_socket.accept()
    threading.Thread(target=network_thread, args=[connection]).start()
print(connection)
