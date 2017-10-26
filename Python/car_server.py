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




def time_op(start, name):
    """Timing function used for debug."""
    tt = time.time() - start
    if timing:
        print('Time taken for %s: %s' % (name, tt))
    return time.time()


def network_thread(inbound_socket):
    """Client handler thread."""
    client_connection = inbound_socket.makefile('rwb')
    connection_up = True
    pr = ProtocolReader()

    def inbound():
        while True:
            while not pr.messageInBuffer:
                print(pr.next_symbol_length)
                inputBytes = client_connection.read(pr.next_symbol_length)
                if inputBytes == b'':
                    connection_up = False
                    return 0
                pr.readBytes(inputBytes)
            print("Got message: %s!" % pr.buf[0:2])
            ch.in_queue.put(pr.unescape_buffer(pr.buf[:]))
            pr.messageInBuffer = False

    def outbound():
        while connection_up:
            message = ch.out_queue.get()
            client_connection.write(message)
            client_connection.flush()

    threading.Thread(target=inbound, daemon=True).start()
    threading.Thread(target=outbound, daemon=True).start()


if __name__ == '__main__':
    inbound_socket = socket.socket()
    inbound_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    inbound_socket.bind(('0.0.0.0', 8000))
    inbound_socket.listen(0)

    image = b'asdf'

    car = CarSerial()
    ch = CommandHandler(car)

    timing = False
    image_lock = threading.RLock()
    connection_lock = threading.RLock()

    while True:
        connection, addr = inbound_socket.accept()
        threading.Thread(target=network_thread, args=[connection]).start()
        print(connection)
