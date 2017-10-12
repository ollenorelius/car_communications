import comms_bytes as cb
import struct


class ProtocolReader:
    """Buffer for messages arriving from network socket."""

    buf = b''
    activeMessage = False
    nextCharEscaped = False
    messageInBuffer = False
    next_symbol_length = 1
    incoming_data_length = False
    def emptyBuffer(self):
        """Small wrapper to make code clearer."""
        self.buf = b''
        self.nextCharEscaped = False
        self.messageInBuffer = False
        self.next_symbol_length = 1

    def readBytes(self, inputBytes):
        """
        Handle a byte package incoming.

        inputBytes is a byte string, representing one symbol. A symbol may be
        a start or end byte  or a data packet.
        """
        if inputBytes not in [b'', b'\x00']:
            print("activeMessage: " + str(self.activeMessage) + " " + str(inputBytes))
        if len(inputBytes) == 1:
            if int.from_bytes(inputBytes, 'big') == cb.START and \
                    self.activeMessage is False:
                self.emptyBuffer()
                self.activeMessage = True
                self.next_symbol_length = 4
                self.incoming_data_length = True
                return 1

            if int.from_bytes(inputBytes, 'big') == cb.END \
                    and self.activeMessage is True:
                self.messageInBuffer = True
                self.activeMessage = False
                self.next_symbol_length = 1
                return 1

        if self.incoming_data_length:
            self.next_symbol_length = struct.unpack('>L', inputBytes)[0]
            self.incoming_data_length = False
            return 1


        if self.activeMessage:
            self.buf += inputBytes
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
        esc_byte = bytes({cb.ESC})
        esc_escaped = bytes({cb.ESC}) + bytes({cb.ESC ^ cb.ESC_XOR})

        start_byte = bytes({cb.START})
        start_escaped = bytes({cb.ESC}) + bytes({cb.START ^ cb.ESC_XOR})

        escaped = buf.replace(start_escaped, start_byte) \
            .replace(esc_escaped, esc_byte)
        return escaped
