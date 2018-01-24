"""Contains class used for reading the protocol."""
import common.comms_bytes as cb
import struct
from common.message import Message


class ProtocolReader:
    """Buffer for messages arriving from connection.

    Used both for socket and serial."""

    buf = b''

    def __init__(self, connection, in_queue):
        """Create a new protocol_reader reading connection into in_queue."""
        self.connection = connection
        self.state = self.state_idle
        self.in_queue = in_queue

    def emptyBuffer(self):
        """Small wrapper to make code clearer."""
        self.buf = b''
        self.next_char_escaped = False
        self.message_in_buffer = False
        self.next_symbol_length = 1

    def state_idle(self):
        """Waiting for a message to start."""
        c = self.connection.read(1)
        # print("Idle... got %s" % c)
        if c == bytes([cb.START]):
            self.state = self.state_get_message
        else:
            pass

    def state_get_message(self):
        """
        Get message body.

        If checksum is OK, add message to inbound message queue.
        """
        c = self.connection.read(1)
        if c != b"~":
            buf = c
        else:
            buf = self.connection.read(1)
        buf += self.connection.read(3)
        ##print("buf is %s" % buf)
        DL = struct.unpack(">L", buf)[0]
        #print("DL is %s" % DL)
        buf = buf + self.connection.read(DL)
        buf = self.unescape_buffer(buf)
        #print(buf)
        msg = Message(buf,source="serial")
        if msg.verify():
            self.in_queue.put(msg)
            self.state = self.state_get_ending
        else:
            self.state = self.state_idle

    def state_get_ending(self):
        """
        Get the ending byte of the message.

        This currently does nothing, since the message ending is defined by
        the DL field of the header.
        """
        if self.connection.read(1) == cb.END:
            self.state = self.state_idle
        else:
            self.state = self.state_idle

    def run(self):
        """Run currently active state."""
        self.state()

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
