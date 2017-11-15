#!/usr/bin/python3
"""Server application running in the background on the Raspberry Pi."""
import socket
import io
try:
    import picamera
    from server.car_serial import CarSerial
except ImportError:
    print("This should be run on the Raspberry Pi!")
import time
import threading
import queue
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
    pr = ProtocolReader()

    def inbound():
        global connection_up
        try:
            while connection_up:
                while not pr.message_in_buffer:
                    print(pr.next_symbol_length)
                    inputBytes = client_connection.read(pr.next_symbol_length)
                    if inputBytes == b'':
                        print("Got empty bytes, shutting down connection")
                        global connection_up
                        connection_up = False
                        return 0
                    pr.readBytes(inputBytes)
                print("Got message: %s!" % pr.buf[0:2])
                pr.message_in_buffer = False
                ch.in_queue.put(pr.unescape_buffer(pr.buf[:]))
            print("Inbound thread closed due to connection_up flag!")
        except ConnectionResetError:
            connection_up = False
            print("Inbound thread closed due to ConnectionResetError!")

    def outbound():
        global connection_up
        while connection_up:
            try:
                message = ch.out_queue.get(timeout=1)
            except queue.Empty:
                pass
            client_connection.write(message)
            client_connection.flush()
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
car = CarSerial()
ch = CommandHandler(car)
image_lock = threading.RLock()
connection_lock = threading.RLock()

timing = False

if __name__ == '__main__':
    run_server()
