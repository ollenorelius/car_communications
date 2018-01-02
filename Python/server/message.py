import struct
import server.comms_bytes as cb
import random

def get_id_generator():
    """Creates generator for message IDs"""
    seed = random.getrandbits(16)
    while True:
        seed += 1
        if seed == 65535:
            seed = 0
        yield seed


id_generator = get_id_generator()


class Message():
    """Container class for messages to be passed between server and Pi."""

    DL = 0
    ID = 0
    reply_to = 0
    time = 0
    group = 0
    command = 0
    data = b''
    chk = 0

    def __init__(self, buf=[]):
        """Create a message from contents of buf."""
        if buf == []:
            self.ID = next(id_generator)
            return 0
        else:
            buf = self.unescape_buffer(buf)
            self.DL = struct.unpack(">L", buf[0:4])[0]
            self.ID = struct.unpack(">H", buf[4:6])[0]
            self.reply_to = struct.unpack(">H", buf[6:8])[0]
            self.time = struct.unpack(">L", buf[8:12])[0]
            self.group = struct.unpack(">B", bytes([buf[12]]))[0]
            self.command = struct.unpack(">B", bytes([buf[13]]))[0]
            self.data = bytes(buf[14:-1])
            self.chk = struct.unpack(">B", bytes([buf[-1]]))[0]

    def get_bytestring(self):
        """Get bytestring representing this message."""
        ret = b''
        ret = b''.join([ret, struct.pack(">L", self.DL)])
        ret = b''.join([ret, struct.pack(">H", self.ID)])
        ret = b''.join([ret, struct.pack(">H", self.reply_to)])
        ret = b''.join([ret, struct.pack(">L", self.time)])
        ret = b''.join([ret, struct.pack(">c", bytes([self.group]))])
        ret = b''.join([ret, struct.pack(">c", bytes([self.command]))])
        ret = b''.join([ret, bytes(self.data)])
        ret = b''.join([ret, struct.pack(">c", bytes([self.get_checksum()]))])
        return self.escape_buffer(ret)

    def get_network_message(self):
        """Get complete message to send over TCP socket."""
        msg = b''
        msg = b''.join([msg, bytes([cb.START])])
        msg = b''.join([msg, self.get_bytestring()])
        msg = b''.join([msg, bytes([cb.END])])
        return msg

    def get_checksum(self):
        """Get checksum of this message."""
        chksum = 0
        ret = b''
        ret = b''.join([ret, struct.pack(">L", self.DL)])
        ret = b''.join([ret, struct.pack(">H", self.ID)])
        ret = b''.join([ret, struct.pack(">H", self.reply_to)])
        ret = b''.join([ret, struct.pack(">L", self.time)])
        ret = b''.join([ret, struct.pack(">c", bytes([self.group]))])
        ret = b''.join([ret, struct.pack(">c", bytes([self.command]))])
        ret = b''.join([ret, bytes(self.data)])
        for b in ret:
            chksum ^= b
        return chksum

    def verify(self):
        """Verify checksum of this message."""
        if self.chk == self.get_checksum():
            return True
        else:
            return False

    def calc_DL(self):
        """
        Get the length of this message.

        This is calculated without the 4 bytes of the data length field itself.
        """
        self.DL = len(self.data) + 11
        return self.DL

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

    def finish(self):
        self.calc_DL()
        self.chk = self.get_checksum()


def pack_short(var):
    return struct.pack(">h", var)


def pack_char(var):
    return struct.pack(">c", var)

def pack_lidar(buf):
    """Pack lidar data for sending to client."""
    data_string = b''
    for data in buf:
        q = struct.pack(">B", data[0])
        a = struct.pack(">H", data[1])
        d = struct.pack(">H", data[2])
        data_string = "".join([data_string, q, a, d])
    return data_string


class Heartbeat(Message):
    def __init__(self):
        Message.__init__(self)
        self.group = cb.HEARTBEAT
        self.finish()


class OK(Message):
    def __init__(self, reply_to):
        Message.__init__(self)
        self.reply_to = reply_to
        self.group = cb.R_OK
        self.finish()


class StopCar(Message):
    def __init__(self):
        Message.__init__(self)
        self.group = cb.CMD_SPEED
        self.command = cb.WHEEL_SPD
        self.data = pack_short(0)
        self.finish()


class SetSpeed(Message):
    def __init__(self, speed):
        Message.__init__(self)
        self.group = cb.CMD_SPEED
        self.command = cb.CAR_SPD
        self.data = pack_short(speed)
        self.finish()


class SetTurnRate(Message):
    def __init__(self, rate):
        Message.__init__(self)
        self.group = cb.CMD_SPEED
        self.command = cb.TURN_SPD
        self.data = pack_short(rate)
        self.finish()


class RequestPicture(Message):
    def __init__(self, identifier):
        Message.__init__(self)
        self.group = cb.REQ_SENS
        self.command = cb.REQ_PIC
        self.data = pack_char(identifier)
        self.finish()


class RequestLidar(Message):
    def __init__(self, id):
        Message.__init__(self)
        self.group = cb.REQ_SENS
        self.command = cb.REQ_LIDAR
        self.data = pack_char(identifier)
        self.finish()


class LidarMessage(Message):
    def __init__(self, data):
        Message.__init__(self)
        self.group = cb.SENS
        self.command = cb.SENS_LIDAR
        self.data = pack_char(identifier)
        self.finish()


class ImageMessage(Message):
    def __init__(self, image):
        Message.__init__(self)
        self.group = cb.SENS
        self.command = cb.SENS_PIC
        self.data = pack_char(identifier)
        self.finish()
