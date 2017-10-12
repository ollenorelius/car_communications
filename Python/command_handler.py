"""A class for parsing ad reacting to inbound network messages."""
import struct
import comms_bytes as cb
from queue import Queue
import threading
try:
    import picamera
except ImportError:
    print("This should be run on the Raspberry Pi!")
import io
import time


class CommandHandler:
    """Parses commands from the buffer in ProtocolReader."""

    car = []
    out_queue = Queue()
    in_queue = Queue()
    image_lock = threading.RLock()
    image = None

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

    def escape_buffer(self, buf):
        """Escape start, end and escape bytes in original message."""
        esc_byte = bytes({cb.ESC})
        esc_escaped = bytes({cb.ESC}) + bytes({cb.ESC ^ cb.ESC_XOR})

        start_byte = bytes({cb.START})
        start_escaped = bytes({cb.ESC}) + bytes({cb.START ^ cb.ESC_XOR})

        escaped = buf.replace(esc_byte, esc_escaped) \
            .replace(start_byte, start_escaped)
        return escaped

    def unescape_buffer(self, buf):
        """Remove effect of escape_buffer."""
        esc_byte = bytes({cb.ESC})
        esc_escaped = bytes({cb.ESC}) + bytes({cb.ESC ^ cb.ESC_XOR})

        start_byte = bytes({cb.START})
        start_escaped = bytes({cb.ESC}) + bytes({cb.START ^ cb.ESC_XOR})

        escaped = buf.replace(start_escaped, start_byte) \
            .replace(esc_escaped, esc_byte)
        return escaped

    def __init__(self, car=None):
        """Constructor. Pass the car object to be controlled."""
        self.car = car
        threading.Thread(target=self.read_in_queue, daemon=True).start()
        threading.Thread(target=self.camera_thread, daemon=True).start()

    def checksum(self, buf):
        """Create a simple checksum by XORing all the bytes in the message."""
        chksum = 0
        for byte in buf:
            chksum ^= byte
        return bytes({chksum})

    def sendOK(self, buf, data=None):
        """
        Send an OK response.

        buf:
             buffer containing message data being replyed to.
        data:
            byte array to append to message.
        """
        print("Sending OK to GS: "
              + str(self.checksum(buf))
              + " data: " + str(data))
        msg = self.create_message(cb.R_OK, None, data, self.checksum(buf))
        self.queue_message(msg)
        return 1

    def queue_message(self, message):
        """Add a message to the outbound network queue."""
        message = bytes({cb.START}) \
            + self.escape_buffer(message) \
            + bytes({cb.END})
        self.out_queue.put(message)

    def read_in_queue(self):
        """Read a message to the inbound network queue."""
        while True:
            message = self.in_queue.get()
            self.handle_message(message)

    def create_message(self, group, command, data, chk=None):
        """Create a message from commands and data."""
        msg = bytes({group})
        if command is not None:
            msg += bytes({command})
        if chk is None:
            if data is not None:
                chk = self.checksum(msg + data)
            else:
                chk = self.checksum(msg)
        msg += chk
        if data is not None:
            msg += data
        return self.escape_buffer(msg)

    def handle_message(self, message):
        """Handle an inbound message."""
        print("handle_message got: " + str(message))
        message = self.unescape_buffer(message)
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
                print('Got picture request!')
                global image
                print("sending picture of size %s" % len(self.image))
                with self.image_lock:
                    img_msg = self.create_message(group=cb.R_OK_IMAGE_FOLLOWS,
                                                  command=None,
                                                  data=self.image)
                print("escaped length %s" % len(img_msg))
                self.sendOK(message, struct.pack('>L', len(img_msg)))
                self.queue_message(img_msg)
                print('sent picture!')
                return 1

        reply = self.car.send_message(group=group, command=command, data=data)
        self.sendOK(message, reply)
