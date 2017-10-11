#!/usr/bin/python3
"""Server application running in the background on the Raspberry Pi."""
import socket
import io
try:
    import picamera
    from car_serial import CarSerial
except ImportError:
    print("This should be run on the Raspberry Pi!")
import time
import threading
from protocol_reader import ProtocolReader
from command_handler import CommandHandler


inbound_socket = socket.socket()
inbound_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
inbound_socket.bind(('0.0.0.0', 8000))
inbound_socket.listen(0)

car = CarSerial()
ch = CommandHandler(car)

timing = False
image_lock = threading.RLock()
connection_lock = threading.RLock()


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

    camera = picamera.PiCamera()
    camera.resolution = (640, 480)
    camera.sensor_mode = 7
    camera.shutter_speed = 10000
    camera.framerate = 40
    camera.rotation = 180

    cam_stream = io.BytesIO()
    for foo in camera.capture_continuous(output=cam_stream,
                                         format='jpeg',
                                         use_video_port=True,
                                         quality=15,
                                         thumbnail=None):
        cam_stream.seek(0)
        with image_lock:
            image = cam_stream.read()
        cam_stream.seek(0)
        cam_stream.truncate()

        # if no clients are connected, just chill ad wait to save power.
        while(threading.active_count() < 3):
            time.sleep(0.2)


def network_thread(inbound_socket):
    """Client handler thread."""
    client_connection = inbound_socket.makefile('rwb')

    def inbound():
        pr = ProtocolReader()
        while True:
            while not pr.messageInBuffer:
                inputByte = client_connection.read(1)
                if inputByte == b'':
                    return 0
                pr.readByte(inputByte)
            print("Got message: %s!" % pr.buf[0:2])
            ch.in_queue.put(pr.buf[:])
            pr.messageInBuffer = False

    def outbound():
        while True:
            message = ch.out_queue.get()
            client_connection.write(message)

    threading.Thread(target=inbound, daemon=True).start()
    threading.Thread(target=outbound, daemon=True).start()




if __name__ == '__main__':
    threading.Thread(target=camera_thread, daemon=True).start()
    while True:
        connection, addr = inbound_socket.accept()
        threading.Thread(target=network_thread, args=[connection]).start()
        print(connection)
