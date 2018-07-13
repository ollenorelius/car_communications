from pathlib import Path
import json
import threading
import car_to_x.CarToCar.enable_car_to_car as c2c_active
import sys
import zmq
import config_pb2 as config_proto
import time
from autonomous.car_controller import CarController

class control_panel:

    TREVOR = "trevor.local"
    AUTONOMOUS = "autonomous-platform.local"

    """with open('%s/config.json' %(Path.home())) as json_data_file:
        data = json.load(json_data_file)"""


    car = CarController("127.0.0.1")

    def init_sockets(self):
        self.context = zmq.Context()
        self.req_socket = self.context.socket(zmq.REQ)
        self.req_socket.connect("tcp://{}:5563".format(self.active_car))

    def update_hardware_info(self):
        self.platform_version = self.data['Car']['Platform Version']
        self.ultrasonic_sensor = self.data['Car']['Sensors'][0]['Ultrasonic']
        self.radar = self.data['Car']['Sensors'][0]['Radar']
        self.camera = self.data['Car']['Sensors'][0]['Camera']
        self.lidar = self.data['Car']['Sensors'][0]['Lidar']

    def update_config(self):
        self.data['Car']['Car_To_Car'] = self.config_dict['Car_To_Car']
        self.data['Car']['SLAM'] = self.config_dict['SLAM']                        
        self.data['Car']['Deep_Learning'] = self.config_dict['Deep_Learning']

        self.req_socket.send_json(self.data, flags = 0, indent = True)
        self.req_socket.recv()

        """#jsonData = json.dumps(self.data)
        with open('%s/config.json' %(Path.home()), 'w') as f:                      
            json.dump(self.data, f, indent=True)"""

    def stop(self):
        self.car.set_speed(0)

    def disarm(self):
        self.car.disarm_motors()

    def arm(self):
        self.car.arm_motors()

    def print_hardware_info(self):
        self.update_hardware_info()
        print("Hardware Info")
        print ("Platform Version: " + json.dumps(self.platform_version, indent = 4))

        print("Ultrasonic:")
        for a in self.ultrasonic_sensor:
            if(self.ultrasonic_sensor[a][0] is True):
                print("\t{name}: {exists}, range: {range}".format(name = a, exists=self.ultrasonic_sensor[a][0], range=self.ultrasonic_sensor[a][1]))
            else:
                print("\t{name}: {exists}".format(name = a, exists=self.ultrasonic_sensor[a][0]))

        print("Radar:")
        for a in self.radar:
            if(self.radar[a][0] is True):
                print("\t{name}: {exists}, range: {range}".format(name = a, exists=self.radar[a][0], range=self.radar[a][1]))
            else:
                print("\t{name}: {exists}".format(name = a, exists=self.radar[a][0]))

        print("Camera:")
        for a in self.camera:
            print("\t{name}: {exists}".format(name = a, exists=self.camera[a]))

        print("{name}: {exists}".format(name = "Lidar", exists = self.lidar)) 

    def print_available_commands(self):
        print("Available commands: ")
        print("help - Displays the available commands")
        print("stop - Stops the car")
        print("arm - Arms the motors")
        print("disarm - Disarms the motors")
        print("hardware_info - Displays hardware related information about the platform")
        print("current_config - Displays the current config of software")
        print("enable_c2c - Enables car to car communications")
        print("disable_c2c - Disables car to car communications")
        print("enable_slam - Enables SLAM")
        print("disable_slam - Disables SLAM")
        print("enable_dl - Enables Deep Learning")
        print("disable_dl - Disables Deep Learning")
 
    def print_config(self):
        for k, v in self.config_dict.items():
            print("{key}: {value}".format(key = k, value = v))
    
    def get_requested_car(self):
        while True:
            print("autonomous - Choose Autonomous-Platform as current platform")
            print("trevor - Choose Trevor as current platform")
            user_input = input('>>> ')
            if(user_input == 'autonomous'):
                self.active_car = self.AUTONOMOUS
                print(chr(27) + "[2J")
                self.init_sockets()
                self.get_config()                                      
                self.get_user_commands()
            elif(user_input == 'trevor'):
                self.active_car = self.TREVOR
                print(chr(27) + "[2J")
                self.init_sockets()
                self.get_config()                                      
                self.get_user_commands()
            else:
                print("Please print a valid command")
                
    def get_config(self):
        self.req_socket.send(b'1')
        data = self.req_socket.recv()
        self.data = json.loads(data.decode())

        print(self.data)

        self.config_dict = {'Car_To_Car': self.data['Car']['Car_To_Car'], 'SLAM': self.data['Car']['SLAM'], 'Deep_Learning': self.data['Car']['Deep_Learning']}
        self.update_hardware_info()
                
    def get_user_commands(self):
        self.print_available_commands()
        while True:
            print("")
            if self.active_car == self.AUTONOMOUS:
                user_input = input('AUTONOMOUS >>> ')
            elif self.active_car == self.TREVOR:
                user_input = input('TREVOR >>> ')
            print("")
            if(user_input == 'help'):
                self.print_available_commands()
            elif(user_input == 'stop'):
                self.stop()
            elif(user_input == 'disarm'):
                self.disarm()
            elif(user_input == 'arm'):
                self.arm()
            elif(user_input == 'hardware_info'):
                self.print_hardware_info()
            elif(user_input == 'current_config'):
                self.print_config()
            elif(user_input == 'enable_c2c'):
                self.enable_c2c()
            elif(user_input == 'disable_c2c'):
                self.disable_c2c()
            elif(user_input == 'enable_slam'):
                self.enable_slam() 
            elif(user_input == 'disable_slam'):
                self.disable_slam()
            elif(user_input == 'enable_dl'):
                self.enable_dl()
            elif(user_input == 'disable_dl'):
                self.disable_dl()
            elif(user_input == 'change_car'):
                self.req_socket.close()
                self.context.term()
                break
            else:
                print("Please enter valid command")
    
    def enable_c2c(self):
        self.config_dict['Car_To_Car'] = True
        self.update_config()
        self.print_config()
    def disable_c2c(self):
        self.config_dict['Car_To_Car'] = False
        self.update_config()
        self.print_config()
    def enable_slam(self):
        self.config_dict['SLAM'] = True
        self.update_config()
        self.print_config()
    def disable_slam(self):
        self.config_dict['SLAM'] = False
        self.update_config()
        self.print_config()
    def enable_dl(self):
        self.config_dict['Deep_Learning'] = True
        self.update_config()
        self.print_config()
    def disable_dl(self):
        self.config_dict['Deep_Learning'] = False
        self.update_config()
        self.print_config()

if __name__ == '__main__':
    panel = control_panel()
    #panel.print_available_commands()
    threading.Thread(target=panel.get_requested_car(), daemon=False).start()
    #threading.Thread(target=panel.get_user_commands, daemon=False).start()
    #threading.Thread(target=panel.config_publisher, daemon=False).start()


"""TODO control panel publishes dict with config info
enable car_to_car shold be moved into ADAS-software
Publish to thesis logs, prints etc"""