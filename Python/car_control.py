"""Logic for car control program."""
from mainwindow import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
import socket
import threading
import io
import struct
from PIL import Image, ImageQt, ImageDraw, ImageFont, ImageOps
import time

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    RC_socket = socket.socket()
    RC_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    RC_socket.connect(('autopi.local', 8000))
    RC_connection = RC_socket.makefile('rwb')

    image_lock = threading.Lock()
    image_stream = io.BytesIO()

    picSize = (640, 480)

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)
        threading.Thread(target=self.camera_thread, daemon=True).start()
        self.setupUi(self)

    def keyPressEvent(self, e):
        if not e.isAutoRepeat():
            if e.key() == QtCore.Qt.Key_Q:
                self.close()
            elif e.key() == QtCore.Qt.Key_W:
                self.RC_connection.write(struct.pack('<c', b'w'))
                self.RC_connection.flush()
            elif e.key() == QtCore.Qt.Key_S:
                self.RC_connection.write(struct.pack('<c', b's'))
                self.RC_connection.flush()
            elif e.key() == QtCore.Qt.Key_A:
                self.RC_connection.write(struct.pack('<c', b'a'))
                self.RC_connection.flush()
            elif e.key() == QtCore.Qt.Key_D:
                self.RC_connection.write(struct.pack('<c', b'd'))
                self.RC_connection.flush()

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            if e.key() == QtCore.Qt.Key_Q:
                self.close()
            elif e.key() == QtCore.Qt.Key_W:
                self.RC_connection.write(struct.pack('<c', b'W'))
                self.RC_connection.flush()
            elif e.key() == QtCore.Qt.Key_S:
                self.RC_connection.write(struct.pack('<c', b'S'))
                self.RC_connection.flush()
            elif e.key() == QtCore.Qt.Key_A:
                self.RC_connection.write(struct.pack('<c', b'A'))
                self.RC_connection.flush()
            elif e.key() == QtCore.Qt.Key_D:
                self.RC_connection.write(struct.pack('<c', b'D'))
                self.RC_connection.flush()

    def camera_thread(self):
        while True:
            self.RC_connection.write(struct.pack('<c', b'p'))
            self.RC_connection.flush()

            image_len = struct.unpack('<L', self.RC_connection.read(struct.calcsize('<L')))[0]
            if not image_len:
                break
            # Construct a stream to hold the image data and read the image
            # data from the NN_connection
            self.image_stream.seek(0)
            self.image_stream.write(self.RC_connection.read(image_len))
            # Rewind the stream, open it as an image with PIL and do some
            # processing on it
            self.image_stream.seek(0)
            temp_image = Image.open(self.image_stream).transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)
            self.picSize = (self.cameraView.size().width(), self.cameraView.size().height())
            temp_image = temp_image.resize(self.picSize)
            with self.image_lock:
                self.bbox_time = time.time()
                image = temp_image
                self.cameraView.setPixmap(QtGui.QPixmap.fromImage(ImageQt.ImageQt(image)))



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
