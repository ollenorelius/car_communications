"""Connection handler for Infotiv Autonomous car platform."""

import serial
import server.comms_bytes as cb
import threading
import time
from server.protocol_reader import ProtocolReader
import struct
import queue
import io
import message as msg
try:
    import picamera
except ImportError:
    print("This should be run on the Raspberry Pi!")
from collections import deque


class VehicleHandler:
    """
    General connection handler for vehicles using
    Infotiv Autonomous Platform.

    Contains methods for handling serial communications asynchronously.
    """

    outbound_serial_queue = queue.Queue()
    inbound_serial_queue = queue.Queue()

    def __init__(self, serial_port='/dev/ttyAMA0', baudrate=115200):
        """
        Constructor for the VehicleHandler.

        serial_port:
            serial_port is the connection string for the arduino serial. On
            linux systems it's typically /dev/ttyAMA0 or /dev/ttyACM0.
            In specific cases it may be /dev/ttyS0 on a Raspberry Pi,
            if hardware serial has been configured that way. If you are
            running this code on Windows, it's COM[something] with no brackets.

        baudrate:
            Integer value of bits per second. Default is 115,200 though other
            common ones are 9,600 and 250,000.
        """
        # Initialize  serial to Arduino
        self.connection = serial.Serial(port=serial_port,
                                        baudrate=baudrate,
                                        timeout=0.2)
        self.pr = ProtocolReader(connection=self.connection,
                                 in_queue=self.inbound_serial_queue)

        # start threads
        threading.Thread(target=self.heartbeat_thread,
                         args=(),
                         daemon=True).start()

        threading.Thread(target=self.serial_reader,
                         args=(),
                         daemon=True).start()

        threading.Thread(target=self.serial_writer,
                         args=(),
                         daemon=True).start()


    def serial_reader(self):
        """Thread function for reading messages from the serial port."""
        while True:
            self.pr.run()

    def serial_writer(self):
        """Thread function for writing messages to the serial port."""
        while True:
            message = self.outbound_serial_queue.get()
            self.connection.write(message.get_network_message())

    def handle_inbound(self):
        """Default inbound serial queue handler"""
        while True:
            message = self.inbound_serial_queue.get()

    def send_message(self, message):
        """Send a message to the DK."""
        self.outbound_serial_queue.put(message)

    def heartbeat_thread(self):
        """Thread method for sending regular heartbeat."""
        while True:
            self.send_message(msg.Heartbeat())
            time.sleep(0.5)


class CarHandler(VehicleHandler):
    """Class for Infotiv car platform.

    This platform has a single camera, and so has one camera thread capturing
    an image into self.image .
    """

    image_lock = threading.RLock()
    lidar_buffer = deque(maxlen=400)

    def __init__(self, serial_port, baudrate):
        VehicleHandler.__init__(self,
                                serial_port=serial_port,
                                baudrate=baudrate)

        threading.Thread(target=self.camera_thread,
                         args=(),
                         daemon=True).start()

    def camera_thread(self):
        """Thread for capturing camera image asynchronously."""
        camera = picamera.PiCamera()
        camera.resolution = (320, 240)
        camera.sensor_mode = 7
        camera.shutter_speed = 10000
        camera.framerate = 40
        camera.rotation = 0

        cam_stream = io.BytesIO()
        for foo in camera.capture_continuous(output=cam_stream,
                                             format='jpeg',
                                             use_video_port=True,
                                             quality=15,
                                             thumbnail=None):
            cam_stream.seek(0)
            with self.image_lock:
                self.image = cam_stream.read()
            cam_stream.seek(0)
            cam_stream.truncate()

            # if no clients are connected, just chill ad wait to save power.
            while(threading.active_count() < 3):
                time.sleep(0.2)

    def handle_inbound(self):
        """Specific serial command handler for Infotiv Car."""
        while True:
            message = self.inbound_serial_queue.get()

            if message.group == cb.SENS:
                if message.command == cb.SENS_LIDAR:
                    map(function, sequence)

    def decode_lidar_chunk(self, chunk):
        """Map a chunk of lidar data into (quality, distance, angle)."""
        quality = struct.unpack(">B", chunk[0])
        angle = struct.unpack(">H", chunk[1:3])
        distance = struct.unpack(">H", chunk[3:5])

    def lidar_chunks(self, buf):
        """Generator for getting lidar data one point at a time."""
        lidar_chunk_size = 5
        for i in range(0, len(buf), lidar_chunk_size):
            yield buf[i:i + lidar_chunk_size]


class TestHandler(VehicleHandler):
    """Class used for unit testing of the Vehicle server."""
    def __init__():
        pass
