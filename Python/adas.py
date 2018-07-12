import threading
import time
import zmq
from pathlib import Path
import json
import common.message as msg
from autonomous.car_controller import CarController
from common import comms_bytes as cb
import config_pb2 as config_proto
import struct
class adas:
    TREVOR = "trevor.local"
    AUTONOMOUS = "autonomous-platform.local"    
    context = zmq.Context()

    stop = False

    dl_message = None
    c2c_message = None
    lane_message = None
    slam_message = None
    def __init__(self):
        self.car = CarController("127.0.0.1")    
        
        self.init_socket()
        threading.Thread(target=self.update_data, daemon=False).start()
        time.sleep(0.1)
        threading.Thread(target=self.check_stop, daemon=False).start()
        threading.Thread(target=self.check_c2c, daemon=False).start()
        threading.Thread(target=self.check_slam, daemon=False).start()
        threading.Thread(target=self.check_dl, daemon=False).start()
        threading.Thread(target=self.run_car, daemon=False).start()
    
    def init_socket(self):
        self.stop_socket = self.context.socket(zmq.REP)
        self.stop_socket.bind("tcp://0.0.0.0:%s" % 5580)

        self.c2c_socket = self.context.socket(zmq.REP)
        self.c2c_socket.setsockopt(zmq.RCVTIMEO, 2000)
        self.c2c_socket.bind("tcp://0.0.0.0:%s" % 5565)

        #self.slam_socket = self.context.socket(zmq.REP)
        #self.slam_socket.bind("tcp://0.0.0.0:%s" % 5566)

        #self.dl_socket = self.context.socket(zmq.REP)
        #self.dl_socket.bind("tcp://0.0.0.0:%s" % 5567)

    def check_stop(self):
        self.stop_socket.recv()
        self.stop = True
        print("STOPPING!")
        self.car.set_speed(0)
        self.stop_socket.send(b'ok')
        time.sleep(2)
        self.stop = False
    
    def update_data(self):
        while True:
            with open('%s/config.json' %(Path.home())) as json_data_file:
                self.data = json.load(json_data_file)
            time.sleep(1)

    def check_c2c(self):
        self.latest_c2c = self.data['Car']['Car_To_Car']
        while True:
            if(self.latest_c2c != self.data['Car']['Car_To_Car']):
                if self.data['Car']['Car_To_Car'] == True: 
                    print("Car To Car is now Active!")
                    self.latest_c2c = self.data['Car']['Car_To_Car']
                else:
                    print("Car To Car is now Inactive!")
                self.latest_c2c = self.data['Car']['Car_To_Car']
            if self.data['Car']['Car_To_Car'] == False:
                self.c2c_message = None
            while self.data['Car']['Car_To_Car']:
                try:
                    self.c2c_message = self.c2c_socket.recv()
                    print("RECEIVING C2C MESSAGE")
                except zmq.Again:
                    print("TRYING TO RECEIVE C2C MESSAGE")
                    continue
                self.c2c_socket.send(b'ok')
                time.sleep(0.1)

    def check_slam(self):
        while self.data['Car']['SLAM']:
            time.sleep(5)
            pass
    def check_dl(self):
        while self.data['Car']['Deep_Learning']:
            time.sleep(5)
            pass
    def check_lane_keeping(self):
        #while self.data['Car']['Lane_Keeping']:
        pass
    
    def run_car(self):
        while True:
            if self.stop:
                message = msg.StopCar()
                self.car.send_message(message)

            else:

                if self.dl_message is not None:
                    dl_message = msg.Message(self.dl_message)
                    print("Deep Learning says: " + str(self.get_info(dl_message)))
                    self.car.send_message(dl_message)
                    self.dl_message = None
                
                elif self.lane_message is not None:
                    lane_message = msg.Message(self.lane_message)
                    print("Lane Keeping says: " + str(self.get_info(lane_message)))
                    self.car.send_message(lane_message)
                    self.lane_message = None
                
                elif self.c2c_message is not None:
                    c2c_message = msg.Message(self.c2c_message)
                    print("Car To Car says: " + str(self.get_info(c2c_message)))
                    self.car.send_message(c2c_message)
                    self.c2c_message = None
                time.sleep(0.5)

    def get_info(self, message):

                    if message.group == cb.CMD_SPEED:
                        if message.command == cb.CAR_SPD:
                            return "Change speed: " + str(struct.unpack(">h", message.data[:2])[0])
                        elif message.command == cb.TURN_SPD:
                            return "Turn: " + str(struct.unpack(">h", message.data[:2])[0])
    


if __name__ == '__main__':
    a = adas()