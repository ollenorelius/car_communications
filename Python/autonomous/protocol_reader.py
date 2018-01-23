"""Contains class used for reading the protocol."""
import common.comms_bytes as cb
import struct


class ProtocolReader:
    """Buffer for messages arriving from network socket."""

    buf = b''
    active_message = False
    next_char_escaped = False
    message_in_buffer = False
    next_symbol_length = 1
    incoming_data_length = False

    def emptyBuffer(self):
        """Small wrapper to make code clearer."""
        self.buf = b''
        self.next_char_escaped = False
        self.message_in_buffer = False
        self.next_symbol_length = 1

    def readBytes(self, input_bytes):
        """
        Handle a byte package incoming.

        input_bytes is a byte string, representing one symbol. A symbol may be
        a start or end byte  or a data packet.
        """
        if input_bytes not in [b'', b'\x00']:
            """print("active_message: "
                  + str(self.active_message)
                  + " " + str(input_bytes))"""
        if len(input_bytes) == 1:
            if int.from_bytes(input_bytes, 'big') == cb.START and \
                    self.active_message is False:
                self.emptyBuffer()
                self.active_message = True
                self.next_symbol_length = 4
                self.incoming_data_length = True
                return 1

            if int.from_bytes(input_bytes, 'big') == cb.END \
                    and self.active_message is True:
                self.message_in_buffer = True
                self.active_message = False
                self.next_symbol_length = 1
                return 1

        if self.incoming_data_length:
            self.next_symbol_length = struct.unpack('>L', input_bytes)[0]
            self.incoming_data_length = False
            return 1

        if self.active_message:
            self.buf += input_bytes
            self.next_symbol_length = 1

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
        escaped = self.escape_buffer(msg)
        return struct.pack('>L', len(escaped)) + escaped

    def checksum(self, buf):
        """Create a simple checksum by XORing all the bytes in the message."""
        chksum = 0
        for byte in buf:
            chksum ^= byte
        return bytes({chksum})

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
        print("Unescaping buffer of length %s" % len(buf))
        esc_byte = bytes({cb.ESC})
        esc_escaped = bytes({cb.ESC}) + bytes({cb.ESC ^ cb.ESC_XOR})

        start_byte = bytes({cb.START})
        start_escaped = bytes({cb.ESC}) + bytes({cb.START ^ cb.ESC_XOR})

        escaped = buf.replace(start_escaped, start_byte) \
            .replace(esc_escaped, esc_byte)
        print("Result has length %s" % len(escaped))
        return escaped

    def get_buffer(self):
        return self.unescape_buffer(self.buf)
