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
import json
from pathlib import Path


import car_to_x.CarToCar.car_to_car as c2c

import zmq

def config_thread(socket):
    while True:
        message = socket.recv()
        if message == 0:
            time.sleep(1)

        elif message == b'1':
            print("Sending config data to control panel")
            with open('%s/config.json' %(Path.home())) as json_data_file:
                data = json.load(json_data_file)
            socket.send_json(data, flags = 0, indent = True)
            message = 0

        else:
            print("Writing to config")
            print(message)
            data = message.decode()
            print(data)
            with open('%s/config.json' %(Path.home()), 'w') as f:
                f.write(data)
            socket.send(b'ok')
            message = 0

def time_op(start, name):
    """Timing function used for debug."""
    tt = time.time() - start
    if timing:
        print('Time taken for %s: %s' % (name, tt))
    return time.time()

latest_cmd = msg.LatestCmdMessage(None)
def publisher_thread(car, socket):
    last_lidar_packet = 0
    last_picture = 0
    last_01_packet = 0
    while True:
        if car.has_image and time.time() - last_picture > 0.05:
            # im_msg = msg.ImageMessage(car.image)
            # Ideally I want to do the above, but it copies too much data,
            # so it slows the transfer down too much.
            socket.send(bytes([cb.SENS, cb.SENS_PIC]) + car.image)
            car.has_image = False
            last_picture = time.time()

        if time.time() - last_01_packet > 0.1:
            socket.send(msg.LidarMessage(list(car.lidar_buffer)).get_zmq_msg())
            socket.send(msg.WheelSpeedMessage(car.current_wheel_speeds).get_zmq_msg())
            socket.send(msg.PropBatteryMessage(car.battery_voltage, car.motor_current).get_zmq_msg())
            socket.send(latest_cmd.get_zmq_msg())
            socket.send(msg.CompassMessage(car.heading).get_zmq_msg())
            socket.send(msg.SonarMessage(car.sonars[0], 0).get_zmq_msg())
            socket.send(msg.SonarMessage(car.sonars[1], 1).get_zmq_msg())
            #socket.send(msg.AccMessage(car.heading).get_zmq_msg())
            #socket.send(msg.GyroMessage(car.heading).get_zmq_msg())
            last_01_packet = time.time()

        time.sleep(0.05)

def network_thread(socket, car):
    """Client handler thread."""
    while True:
        raw = socket.recv()
        inbound = msg.Message(raw)

        if inbound.group not in [1] and not inbound.c2c == 255:
            global latest_cmd
            latest_cmd = msg.LatestCmdMessage(inbound.get_zmq_msg())
            print("NETWORK THREAD: Got c2c %s, prio %s, group %s, command %s, data %s" % (inbound.c2c,
                                                         inbound.prio,
                                                         inbound.group,
                                                         inbound.command,
                                                         inbound.data))
        if inbound.c2c == 255:
            print("Network thread got message from c2c")
        car.send_message(inbound, inbound.prio)
        socket.send(msg.OK(0).get_zmq_msg())

def run_server():
    image = b''
    car = CarHandler(serial_port='/dev/ttyAMA0', baudrate=1000000)

    server_context = zmq.Context()

    config_socket = server_context.socket(zmq.REP)
    config_socket.bind("tcp://0.0.0.0:5563")

    publish_socket = server_context.socket(zmq.PUB)
    publish_socket.setsockopt(zmq.SNDHWM, 1)
    publish_socket.setsockopt(zmq.SNDBUF, 2048)
    publish_socket.bind("tcp://*:5556")

    command_socket = server_context.socket(zmq.REP)
    command_socket.bind("tcp://*:5555")

    threading.Thread(target=publisher_thread, args=[car, publish_socket], daemon=True).start()
    threading.Thread(target=network_thread, args=[command_socket, car], daemon=False).start()
    threading.Thread(target=config_thread, args=[config_socket], daemon=False).start()
    print("Car server online, awaiting connections")

    car2car = c2c.car_to_car(server_context)
    



timing = False

if __name__ == '__main__':
    run_server()
