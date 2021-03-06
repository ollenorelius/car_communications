"""Connection handler for Infotiv Autonomous car platform."""

import serial
import common.comms_bytes as cb
import threading
import time
from server.protocol_reader import ProtocolReader
import struct
import queue
import io
import common.message as msg
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

    outbound_serial_queue = queue.PriorityQueue()
    inbound_serial_queue = queue.Queue()

    def __init__(self, serial_port='/dev/ttyAMA0', baudrate=2000000):
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
            tmptime = time.time()
            message = self.outbound_serial_queue.get()
            #print("Sending %s to car" % message.get_serial_msg())
            if not (tmptime - message[1][1] > message[1][0]): #if not timeout
                self.connection.write(message[1][2].get_serial_msg())
            else:
                print("Message timeout")
            if(self.outbound_serial_queue.qsize() > 200): #If queue "full" empt$
                self.clear_queue()

    def clear_queue(self):
        tmpqueue = queue.PriorityQueue()
        while(self.outbound_serial_queue.qsize() > 0): #clear queue
            tmptime = time.time()
            tmpvalue = self.outbound_serial_queue.get()
            if not (tmptime - tmpvalue[1][1] > tmpvalue[1][0]): #save the valid entries
                tmpqueue.put(tmpvalue)
        self.outbound_serial_queue.queue = copy.deepcopy(tmpqueue.queue) #copy tmpqueue

    def handle_inbound(self):
        """Default inbound serial queue handler. Discards messages."""
        while True:
            message = self.inbound_serial_queue.get()

    def send_message(self, message, prio = 10):
        """Send a message to the DK."""
        self.outbound_serial_queue.put((prio, [1, time.time(), message]))


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
    current_speed = 0
    current_turn_rate = 0
    current_wheel_speeds = [0, 0, 0, 0]
    battery_voltage = 0
    motor_current = 0
    heading = 0
    sonars = [0,0,0,0]

    has_image = False

    def __init__(self, serial_port='/dev/ttyAMA0', baudrate=2000000):
        VehicleHandler.__init__(self,
                                serial_port=serial_port,
                                baudrate=baudrate)

        threading.Thread(target=self.camera_thread,
                         args=(),
                         daemon=True).start()
        threading.Thread(target=self.handle_inbound,
                         args=(),
                         daemon=True).start()

    def camera_thread(self):
        """Thread for capturing camera image asynchronously."""
        camera = picamera.PiCamera()
        camera.resolution = (640, 480)
        #camera.sensor_mode = 7
        #camera.shutter_speed = 10000
        camera.framerate = 30
        camera.rotation = 180

        cam_stream = io.BytesIO()
        for foo in camera.capture_continuous(output=cam_stream,
                                             format='jpeg',
                                             use_video_port=True,
                                             quality=15,
                                             thumbnail=None):
            cam_stream.seek(0)
            with self.image_lock:
                self.image = cam_stream.read()
            self.has_image = True
            cam_stream.seek(0)
            cam_stream.truncate()

            # if no clients are connected, just chill ad wait to save power.

            while(threading.active_count() < 3):
                pass

    def handle_inbound(self):
        """Specific serial command handler for Infotiv Car."""
        t = 0
        while True:
            message = self.inbound_serial_queue.get()
            if message.group == cb.SENS:
                if message.command == cb.SENS_LIDAR:
                    if len(message.data) % 5 != 0:
                        print("Got invalid lidar packet, len is %s!"
                              % len(message.data))
                        continue
                    #print("raw lidar data is %d", message.data)
                    lidardata = map(self.decode_lidar_chunk,
                                    self.lidar_chunks(message.data))

                    self.lidar_buffer.extend(list(lidardata))

                elif message.command == cb.SENS_SPEED:
                    ret = struct.unpack(">hh", message.data)
                    self.current_speed = ret[0]
                    self.current_turn_rate = ret[1]
                elif message.command == cb.SENS_WHEEL:
                    wheels = struct.unpack(">hhhh", message.data)
                    self.current_wheel_speeds = wheels
                elif message.command == cb.SENS_P_BATT:
                    data = struct.unpack(">hh", message.data)
                    self.battery_voltage = data[0]
                    self.motor_current = data[1]
                elif message.command == cb.SENS_COMPASS:
                    heading = struct.unpack(">h", message.data)[0]
                    self.heading = heading
                elif message.command == cb.SENS_SONAR:
                    dist, index = struct.unpack(">hB", message.data)
                    if index in range(4):
                        self.sonars[index] = dist

            elif message.group == cb.CMD_STATUS:
                if message.command == cb.HEARTBEAT:
                    pass
                if message.command == cb.HANDSHAKE:
                    pass
                if message.command == cb.ASK_STATUS:
                    pass

            if time.time() - t > 1:
                t = time.time()
                min_dist = 100000
                ang = -1
                for d in self.lidar_buffer:
                    if d[1] < min_dist and d[0] > 1:
                        min_dist = d[1]
                        ang = d[2]


    def decode_lidar_chunk(self, chunk):
        """Map a chunk of lidar data into (quality, distance, angle)."""
        #print("decoding chunk: %s" % chunk)
        return struct.unpack(">BHH", chunk)

    def lidar_chunks(self, buf):
        """Generator for getting lidar data one point at a time."""
        lidar_chunk_size = 5
        for i in range(0, len(buf), lidar_chunk_size):
            yield buf[i:i + lidar_chunk_size]


class TestHandler(VehicleHandler):
    """Class used for unit testing of the Vehicle server."""
    def __init__():
        pass
