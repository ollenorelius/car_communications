#!/usr/bin/python3
"""Server application running in the background on the Raspberry Pi."""
import socket
import io
try:
    import picamera
    from server.car_handler import CarHandler
except ImportError:
    print("This should be run on the Raspberry Pi!")
import time
import threading
import queue
from queue import Queue
from server.protocol_reader import ProtocolReader
from server.command_handler import CommandHandler


def time_op(start, name):
    """Timing function used for debug."""
    tt = time.time() - start
    if timing:
        print('Time taken for %s: %s' % (name, tt))
    return time.time()


def network_thread(inbound_socket):
    """Client handler thread."""
    client_connection = inbound_socket.makefile('rwb')
    global connection_up
    connection_up = True
    inbound_queue = Queue()
    outbound_queue = Queue()
    pr = ProtocolReader(client_connection, inbound_queue)
    ch = CommandHandler(car, inbound_queue, outbound_queue)

    def inbound():
        global connection_up
        try:
            while connection_up:
                pr.run()
            print("Inbound thread closed due to connection_up flag!")
        except ConnectionResetError:
            connection_up = False
            print("Inbound thread closed due to ConnectionResetError!")

    def process():
        global connection_up
        while connection_up:
            ch.handle_message()

    def outbound():
        global connection_up
        while connection_up:
            try:
                message = outbound_queue.get(timeout=1)
                msg_bytes = message.get_network_message()
                client_connection.write(msg_bytes)
            except queue.Empty:
                pass
        print("Outbound thread closed!")

    threading.Thread(target=inbound, daemon=True).start()
    threading.Thread(target=outbound, daemon=True).start()
    while connection_up:
        pass
    ch.stop_car()


def run_server():
    inbound_socket = socket.socket()
    inbound_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    inbound_socket.bind(('0.0.0.0', 8000))
    inbound_socket.listen(0)

    try:
        threading.Thread(target=camera_thread, daemon=True).start()
    except picamera.exc.PiCameraMMALError:
        print("Could not init camera!")
    except picamera.exc.PiCameraError:
        print("Could not init camera! Make sure it is plugged in right, and then run sudo raspi-config")

    print("Car server online, awaiting connections")

    while True:
        global connection_up

        connection, addr = inbound_socket.accept()
        connection_up = False
        time.sleep(1)
        connection_up = True
        threading.Thread(target=network_thread, args=[connection]).start()
        print(connection)


image = b''
car = CarHandler()
image_lock = threading.RLock()
connection_lock = threading.RLock()

timing = False

if __name__ == '__main__':
    run_server()
