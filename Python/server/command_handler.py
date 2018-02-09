"""A class for parsing ad reacting to inbound network messages."""
import struct
import common.comms_bytes as cb
from queue import Queue
import threading
import io
import time
from server.protocol_reader import ProtocolReader
import common.message as msg


class CommandHandler:
    """Parses commands from the buffer in ProtocolReader."""

    def __init__(self, car, inbound_queue, outbound_queue):
        """Constructor. Pass the car object to be controlled."""
        self.car = car
        self.in_queue = inbound_queue
        self.out_queue = outbound_queue
        threading.Thread(target=self.read_in_queue, daemon=True).start()

    def sendOK(self, reply_to):
        """
        Send an OK response.

        reply_to: ID of message being replied to.
        """
        self.out_queue.put(msg.OK(reply_to=reply_to))
        return 1

    def read_in_queue(self):
        """Read a message to the inbound network queue."""
        while True:
            message = self.in_queue.get()
            self.handle_message(message)

    def stop_car(self):
        """Sends command immediately stopping car."""
        print("stopping car!")
        self.car.send_message(msg.StopCar())

    def handle_message(self, message):
        """Handle an inbound message."""

        print("handle_message got: " + str(message))
        group = message.group
        command = message.command
        data = message.data

        # Use these to override functionality if desired.
        if group == cb.CMD_STATUS:
            if command == cb.HEARTBEAT:
                pass
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
                # print('Got picture request!')
                global image
                # print("sending picture of size %s" % len(self.image))
                with self.image_lock:
                    img_msg = self.out_queue.put(msg.ImageMessage(image))
                #print("escaped length %s" % len(img_msg))
                #print('sent picture!')
                return 1
            elif command == cb.REQ_LIDAR:
                pass


        self.car.send_message(message=message)
