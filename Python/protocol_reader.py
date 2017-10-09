import comms_bytes as cb


class ProtocolReader:
    """Buffer for messages arriving from network socket."""

    buf = []
    activeMessage = False
    nextCharEscaped = False
    messageInBuffer = False

    def emptyBuffer(self):
        """Small wrapper to make code clearer."""
        self.buf = []
        self.nextCharEscaped = False
        self.messageInBuffer = False

    def readByte(self, inputByte):
        """
        Handle a single byte incoming.

        inputByte is a single byte char.
        """
        print(str(self.activeMessage) + str(inputByte))
        if int.from_bytes(inputByte, 'big') == cb.START and \
                self.activeMessage is False:
            self.emptyBuffer()
            self.activeMessage = True
            return 1

        if int.from_bytes(inputByte, 'big') == cb.END and self.activeMessage is True:
            self.messageInBuffer = True
            self.activeMessage = False
            return 1

        elif int.from_bytes(inputByte, 'big') == cb.ESC:
            self.nextCharEscaped = True
            return 1

        if self.nextCharEscaped:
            inputByte = bytes(int.from_bytes(inputByte, 'big') ^ cb.ESC_XOR)
            self.nextCharEscaped = False
        if self.activeMessage:
            self.buf.append(inputByte)
