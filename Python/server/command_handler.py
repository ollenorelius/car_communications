"""A class for parsing ad reacting to inbound network messages."""
import struct
import server.comms_bytes as cb
from queue import Queue
import threading
try:
    import picamera
except ImportError:
    print("This should be run on the Raspberry Pi! (If you are running on the Pi, something's up with the camera. Check the connection.)")
import io
import time
from server.protocol_reader import ProtocolReader


class CommandHandler:
    """Parses commands from the buffer in ProtocolReader."""

    car = []
    out_queue = Queue()
    in_queue = Queue()
    image_lock = threading.RLock()
    image = None
    pr = ProtocolReader()

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

    def __init__(self, car=None):
        """Constructor. Pass the car object to be controlled."""
        self.car = car
        threading.Thread(target=self.read_in_queue, daemon=True).start()
        try:
            threading.Thread(target=self.camera_thread, daemon=True).start()
        except picamera.exc.PiCameraMMALError:
            print("Could not init camera!")
        except picamera.exc.PiCameraError:
            print("Could not init camera! Make sure it is plugged in right, and then run sudo raspi-config")

    def sendOK(self, buf, data=None):
        """
        Send an OK response.

        buf:
             buffer containing message data being replyed to.
        data:
            byte array to append to message.
        """
        print("Sending OK to GS: "
              + str(self.pr.checksum(buf))
              + " data: " + str(data))
        msg = self.pr.create_message(cb.R_OK, None, data, self.pr.checksum(buf))
        self.queue_message(msg)
        return 1

    def queue_message(self, message):
        """Add a message to the outbound network queue."""
        message = bytes({cb.START}) \
            + message \
            + bytes({cb.END})
        self.out_queue.put(message)

    def read_in_queue(self):
        """Read a message to the inbound network queue."""
        while True:
            message = self.in_queue.get()
            self.handle_message(message)

    def stop_car(self):
        print("stopping car!")
        self.car.send_message(group=cb.CMD_SPEED, command=cb.TURN_SPD, data=struct.pack('>h', 0))
        self.car.send_message(group=cb.CMD_SPEED, command=cb.CAR_SPD, data=struct.pack('>h', 0))

    def handle_message(self, message):
        """Handle an inbound message."""
        print("handle_message got: " + str(message))
        group = message[0]
        command = message[1]
        data = message[2:]
        # Use these to override functionality if desired.
        if group == cb.CMD_STATUS:
            if command == cb.HEARTBEAT:
                self.sendOK(message, data=None)
                return 1
            elif command == cb.HANDSHAKE:
                pass
            elif command == cb.ASK_STATUS:
                pass

        elif group == cb.CMD_SPEED:
            if command == cb.WHEEL_SPD:
                pass
            elif command == cb.CAR_SPD:
                pass
            elif command == cb.TURN_SPD:
                pass

        elif group == cb.CMD_SPEED_CL:
            if command == cb.DIST_CL:
                pass
            elif command == cb.TURN_CL:
                pass
            elif command == cb.TURN_ABS_CL:
                pass

        elif group == cb.REQ_SENS:
            if command == cb.REQ_COMPASS:
                pass
            elif command == cb.REQ_ACC:
                pass

            elif command == cb.REQ_GYRO:
                pass
            elif command == cb.REQ_PIC:
                #print('Got picture request!')
                global image
                #print("sending picture of size %s" % len(self.image))
                with self.image_lock:
                    img_msg = self.pr.create_message(
                                                  group=cb.R_OK_IMAGE_FOLLOWS,
                                                  command=None,
                                                  data=self.image)
                #print("escaped length %s" % len(img_msg))
                self.queue_message(img_msg)
                #print('sent picture!')
                return 1

        reply = self.car.send_message(group=group, command=command, data=data)
        self.sendOK(message, reply)
