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
    with open('%s/config.json' %(Path.home())) as json_data_file:
        data = json.load(json_data_file)

    config_dict = {'Car_To_Car': data['Car']['Car_To_Car'], 'SLAM': data['Car']['SLAM'], 'Deep_Learning': data['Car']['Deep_Learning']}

    car = CarController("127.0.0.1")

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

        #jsonData = json.dumps(self.data)
        with open('%s/config.json' %(Path.home()), 'w') as f:
            json.dump(self.data, f, indent=True)

        """self.proto_config.Car_To_Car = self.config_dict['Car_To_Car']
        self.proto_config.SLAM = self.config_dict['SLAM']                       #FOR USING PROTOBUF
        self.proto_config.Deep_Learning = self.config_dict['Deep_Learning']"""

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

    """def config_publisher(self):
        context = zmq.Context()
        config_socket = context.socket(zmq.PUB)
        config_socket.bind("tcp://*:5558")

        while True:
            self.proto_config = config_proto.Config()                           #FOR PUBLISHING THE PROOBUF OBJECT
            self.update_config()
            #print("This is what im sending!")
            #print(self.proto_config.Car_To_Car)
            #print(self.proto_config.SLAM)
            #print(self.proto_config.Deep_Learning)
            config_socket.send(self.proto_config.SerializeToString())
            time.sleep(1)"""
    
    def get_user_commands(self):
        while True:
            print("")
            user_input = input('>>> ')
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
    panel.update_hardware_info()
    panel.print_available_commands()
    threading.Thread(target=panel.get_user_commands, daemon=False).start()
    #threading.Thread(target=panel.config_publisher, daemon=False).start()


"""TODO control panel publishes dict with config info
enable car_to_car shold be moved into ADAS-software
Publish to thesis logs, prints etc"""