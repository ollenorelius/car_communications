"""Logic for car control program."""
from mainwindow import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
import threading
from PIL import Image, ImageQt, ImageDraw, ImageFont, ImageOps
import time
from autonomous.car_controller import CarController


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    image_lock = threading.Lock()

    car = CarController(address='autonomous-platform.local', port=8000)

    picSize = (1920, 1080)
    speed = 0
    turn = 0

    def set_speed(self, s): self.speed = s

    def set_turnrate(self, t): self.turn = t

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)
        threading.Thread(target=self.camera_thread, daemon=True).start()
        threading.Thread(target=self.command_thread, daemon=True).start()
        self.setupUi(self)

        self.key_down_actions = {
            QtCore.Qt.Key_W: self.set_speed,
            QtCore.Qt.Key_S: self.set_speed,
            QtCore.Qt.Key_A: self.set_turnrate,
            QtCore.Qt.Key_D: self.set_turnrate,
            QtCore.Qt.Key_Q: self.close
        }

        self.key_arguments = {
            QtCore.Qt.Key_W: 250,
            QtCore.Qt.Key_S: -250,
            QtCore.Qt.Key_A: 150,
            QtCore.Qt.Key_D: -150,
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
            if self.key_arguments[e.key()] is not None:
                self.key_down_actions[e.key()](self.key_arguments[e.key()])
            else:
                self.key_down_actions[e.key()]()

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            if self.key_arguments[e.key()] is not None:
                self.key_up_actions[e.key()](0)
            else:
                self.key_up_actions[e.key()]()

    def camera_thread(self):
        while True:
            time.sleep(0.0)
            temp_image = self.car.get_picture(0)
            if temp_image is not None:
                self.picSize = (self.cameraView.size().width(),
                                self.cameraView.size().height())
                temp_image = temp_image.resize(self.picSize)
                with self.image_lock:
                    self.bbox_time = time.time()
                    image = temp_image
                    self.cameraView.setPixmap(
                                QtGui.QPixmap.fromImage(ImageQt.ImageQt(image)))

    def command_thread(self):
        while True:
            self.car.set_speed(self.speed)
            self.car.set_turnrate(self.turn)
            print("Turn rate: %s, speed: %s-----------------------------------------" % (self.turn, self.speed))
            time.sleep(0.2)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
