"""Logic for car control program."""
from mainwindow import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
import threading
from PIL import Image, ImageQt, ImageDraw, ImageFont, ImageOps
import time
from car_controller import CarController


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    image_lock = threading.Lock()

    car = CarController(address='autopi.local', port=8000)

    picSize = (640, 480)

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)
        threading.Thread(target=self.camera_thread, daemon=True).start()
        self.setupUi(self)

        self.key_down_actions = {
            QtCore.Qt.Key_W: self.car.set_speed,
            QtCore.Qt.Key_S: self.car.set_speed,
            QtCore.Qt.Key_A: self.car.set_turnrate,
            QtCore.Qt.Key_D: self.car.set_turnrate,
            QtCore.Qt.Key_Q: self.close
        }

        self.key_arguments = {
            QtCore.Qt.Key_W: 127,
            QtCore.Qt.Key_S: -127,
            QtCore.Qt.Key_A: 100,
            QtCore.Qt.Key_D: -100,
            QtCore.Qt.Key_Q: None
        }

        self.key_up_actions = {
            QtCore.Qt.Key_W: self.car.set_speed,
            QtCore.Qt.Key_S: self.car.set_speed,
            QtCore.Qt.Key_A: self.car.set_turnrate,
            QtCore.Qt.Key_D: self.car.set_turnrate,
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
            time.sleep(0.1)
            temp_image = self.car.get_picture(0)
            if temp_image != None:
                self.picSize = (self.cameraView.size().width(),
                                self.cameraView.size().height())
                temp_image = temp_image.resize(self.picSize)
                with self.image_lock:
                    self.bbox_time = time.time()
                    image = temp_image
                    self.cameraView.setPixmap(
                                QtGui.QPixmap.fromImage(ImageQt.ImageQt(image)))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
