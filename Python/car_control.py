"""Logic for car control program."""
from mainwindow import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
import threading
from PIL import Image, ImageQt, ImageDraw, ImageFont, ImageOps
import time
from autonomous.car_controller import CarController

import numpy as np
from matplotlib import pyplot as plt
import matplotlib.image as mpimg
import matplotlib.animation as animation
import matplotlib.cm as cm


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    image_lock = threading.Lock()

    car = CarController(address="autonomous-platform.local")

    picSize = (800, 600)
    speed = 0
    turn = 0

    def set_speed(self, s):
        self.speed = s
        self.car.set_speed(self.speed)
        self.car.set_turnrate(self.turn)

    def set_turnrate(self, t):
        self.turn = t
        self.car.set_speed(self.speed)
        self.car.set_turnrate(self.turn)

    def updatelidar(self, *args):
        data = self.car.get_lidar()
        if len(data) > 1:
            data = data*[1, 0.25, (1/64)/180*np.pi]
            x = -data[:50, 2] + np.pi*0.5
            y = data[:50, 1]
            d = np.column_stack((x, y))
            self.c.set_offsets(d)
            self.c.set_color(cm.hsv(y/max(y)))
        plt.pause(0.05)
        return self.c,

    def __init__(self, parent=None):
        """self.fig = plt.figure()
        plt.ion()
        self.ax = self.fig.add_subplot(111, projection="polar")

        data = self.car.get_lidar()
        self.c = self.ax.scatter(-data[:50,2] + np.pi,
                                 data[:50,1],
                                 c=data[:50,1],
                                 s=50,
                                 cmap='hsv',
                                 alpha=0.75)
        plt.pause(0.1)

        ani2 = animation.FuncAnimation(self.fig, self.updatelidar, interval=1, blit=True)
        plt.pause(0.1)"""
        QtWidgets.QMainWindow.__init__(self, parent=parent)
        threading.Thread(target=self.camera_thread, daemon=True).start()
        threading.Thread(target=self.command_thread, daemon=True).start()
        self.setupUi(self)

        self.key_down_actions = {
            QtCore.Qt.Key_W: self.set_speed,
            QtCore.Qt.Key_S: self.set_speed,
            QtCore.Qt.Key_A: self.set_turnrate,
            QtCore.Qt.Key_D: self.set_turnrate,
            QtCore.Qt.Key_Q: self.close,
            QtCore.Qt.Key_R: self.car.arm_motors,
            QtCore.Qt.Key_T: self.car.disarm_motors
        }

        self.key_arguments = {
            QtCore.Qt.Key_W: 550,
            QtCore.Qt.Key_S: -350,
            QtCore.Qt.Key_A: 250,
            QtCore.Qt.Key_D: -250,
            QtCore.Qt.Key_Q: None
        }

        self.key_up_actions = {
            QtCore.Qt.Key_W: self.set_speed,
            QtCore.Qt.Key_S: self.set_speed,
            QtCore.Qt.Key_A: self.set_turnrate,
            QtCore.Qt.Key_D: self.set_turnrate,
            QtCore.Qt.Key_Q: self.close
        }

    def keyPressEvent(self, e):
        if not e.isAutoRepeat():
            if e.key() in self.key_down_actions:
                if e.key() in self.key_arguments \
                and self.key_arguments[e.key()] is not None:
                    self.key_down_actions[e.key()](self.key_arguments[e.key()])
                else:
                    self.key_down_actions[e.key()]()

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            if e.key() in self.key_up_actions:
                if e.key() in self.key_arguments \
                and self.key_arguments[e.key()] is not None:
                    self.key_up_actions[e.key()](0)
                else:
                    self.key_up_actions[e.key()]()

    def camera_thread(self):
        while True:
            temp_image = self.car.get_picture(0)

            #self.picSize = (self.cameraView.size().width(),
            #                self.cameraView.size().height())
            temp_image = temp_image.resize(self.picSize)
            image = temp_image
            print(self.car.get_wheel_speeds())
            self.cameraView.setPixmap(
                        QtGui.QPixmap.fromImage(ImageQt.ImageQt(image)))

    def command_thread(self):
        while True:
            self.car.set_speed(self.speed)
            self.car.set_turnrate(self.turn)
            time.sleep(0.5)



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
