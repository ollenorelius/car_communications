#!/usr/bin/python3
"""Server application running in the background on the Raspberry Pi."""
import socket
import io
try:
    from server.car_handler import CarHandler
except ImportError:
    print("This should be run on the Raspberry Pi!")
import time
import threading
import queue
from queue import Queue
from server.protocol_reader import ProtocolReader
from server.command_handler import CommandHandler
import common.message as msg
import common.comms_bytes as cb

import zmq


def time_op(start, name):
    """Timing function used for debug."""
    tt = time.time() - start
    if timing:
        print('Time taken for %s: %s' % (name, tt))
    return time.time()


def publisher_thread(car, socket):
    last_lidar_packet = 0
    last_picture = 0
    last_speed_packet = 0
    while True:
        if car.has_image and time.time() - last_picture > 0.05:
            # im_msg = msg.ImageMessage(car.image)
            # Ideally I want to do the above, but it copies too much data,
            # so it slows the transfer down too much.
            socket.send(bytes([cb.SENS, cb.SENS_PIC]) + car.image)
            car.has_image = False
            last_picture = time.time()

        if time.time() - last_lidar_packet > 0.1:
            socket.send(msg.LidarMessage(list(car.lidar_buffer)).get_zmq_msg())
            last_lidar_packet = time.time()

        if time.time() - last_speed_packet > 0.1:
            socket.send(msg.WheelSpeedMessage(car.current_wheel_speeds).get_zmq_msg())
            last_speed_packet = time.time()
        time.sleep(0.05)




def network_thread(socket, car):
    """Client handler thread."""
    while True:
        inbound = msg.Message(socket.recv())
        if inbound.group not in [16, 1]:
            print("Got group %s, command %s, data %s" % (inbound.group,
                                                         inbound.command,
                                                         inbound.data))
        car.send_message(inbound)
        socket.send(msg.OK(0).get_zmq_msg())




def run_server():
    image = b''
    car = CarHandler(serial_port='/dev/ttyAMA0', baudrate=2000000)

    server_context = zmq.Context()

    publish_socket = server_context.socket(zmq.PUB)
    publish_socket.setsockopt(zmq.SNDHWM, 1)
    publish_socket.setsockopt(zmq.SNDBUF, 2048)
    publish_socket.bind("tcp://*:5556")

    command_socket = server_context.socket(zmq.REP)
    command_socket.bind("tcp://*:5555")

    threading.Thread(target=publisher_thread, args=[car, publish_socket], daemon=True).start()
    threading.Thread(target=network_thread, args=[command_socket, car], daemon=False).start()
    print("Car server online, awaiting connections")





timing = False

if __name__ == '__main__':
    run_server()
