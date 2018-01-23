"""
Unit tests for the server application.

May need to be run on the Raspberry Pi.
"""

import common.message as msg
import unittest


escaper = msg.Message.escape_buffer
deescaper = msg.Message.unescape_buffer


class server_tests(unittest.TestCase):
    """Main test class."""

    esc_inputs = [b'\x7d\x7e',
                  b'\x7d\x7e\x7e',
                  b'}^}^',
                  b'}}^']
    esc_results = [b'\x7d\x5d\x7d\x5e',
                   b'\x7d\x5d\x7d\x5e\x7d\x5e',
                   b'}]^}]^',
                   b'}]}]^']

    random_data = [b'{[]}{{[[9]]][}}}}}}]}}',
                   b'sdfgs{[}[^^^^^}}]]]]}}}~~~~~}}}',
                   b's}df}gs{[}[^^}}]]}~}}~~}}}',
                   b'sd}]f~g}s}{[}[^}}]]}]}]}}~}}}']

    def test_escape_buffer(self):
        """Test that escaping characters works."""
        test_count = len(self.esc_inputs)
        for i in range(test_count):
            self.assertEqual(
                escaper(0, buf=self.esc_inputs[i]), self.esc_results[i])

    def test_unescape_buffer(self):
        """Test that de-escaping characters works."""
        test_count = len(self.esc_inputs)
        for i in range(test_count):
            self.assertEqual(
                deescaper(0, buf=self.esc_results[i]), self.esc_inputs[i])

    def test_escape_loop(self):
        """Integration test of escaping data."""
        for d in self.random_data:
            forward = escaper(0, d)
            backward = deescaper(0, forward)
            self.assertEqual(d, backward)
        for d in self.esc_inputs:
            forward = escaper(0, d)
            backward = deescaper(0, forward)
            self.assertEqual(d, backward)
        for d in self.esc_results:
            forward = escaper(0, d)
            backward = deescaper(0, forward)
            self.assertEqual(d, backward)

    def test_OK_msg(self):
        message = msg.OK(reply_to=1234)
        reconstruct = msg.Message(message.get_bytestring())
        self.assertEqual(message.DL, reconstruct.DL)
        self.assertEqual(message.ID, reconstruct.ID)
        self.assertEqual(message.reply_to, reconstruct.reply_to)
        self.assertEqual(message.time, reconstruct.time)
        self.assertEqual(message.group, reconstruct.group)
        self.assertEqual(message.command, reconstruct.command)
        self.assertEqual(message.chk, reconstruct.chk)
        self.assertEqual(message.data, reconstruct.data)


    def test_speed_msg(self):
        message = msg.SetSpeed(speed=0x7E)
        reconstruct = msg.Message(message.get_bytestring())
        self.assertEqual(message.DL, reconstruct.DL)
        self.assertEqual(message.ID, reconstruct.ID)
        self.assertEqual(message.reply_to, reconstruct.reply_to)
        self.assertEqual(message.time, reconstruct.time)
        self.assertEqual(message.group, reconstruct.group)
        self.assertEqual(message.command, reconstruct.command)
        self.assertEqual(message.chk, reconstruct.chk)
        self.assertEqual(message.data, reconstruct.data)

if __name__ == '__main__':
    unittest.main()
