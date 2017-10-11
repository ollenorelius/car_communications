import car_server
import unittest


class server_tests(unittest.TestCase):
    def test_escape_buffer(self):
        ch = car_server.CommandHandler()
        input_buffers = [b'\xff\x64\x34\x7d\x7e',
                         b'\x7d\x64\x34\x7e\x7e']

        result_buffers = [b'\xff\x64\x34\x7d\x5d\x7d\x5e',
                          b'\x7d\x5d\x64\x34\x7d\x5e\x7d\x5e']
        test_count = len(input_buffers)
        for i in range(test_count):
            self.assertEqual(
                ch.escape_buffer(
                    buf=input_buffers[i]), result_buffers[i])

    def test_unescape_buffer(self):
        ch = car_server.CommandHandler()
        input_buffers = [b'\xff\x64\x34\x7d\x5d\x7d\x5e',
                         b'\x7d\x5d\x64\x34\x7d\x5e\x7d\x5e']
        result_buffers = [b'\xff\x64\x34\x7d\x7e',
                          b'\x7d\x64\x34\x7e\x7e']

        test_count = len(input_buffers)
        for i in range(test_count):
            self.assertEqual(
                ch.unescape_buffer(
                    buf=input_buffers[i]), result_buffers[i])


if __name__ == '__main__':
    unittest.main()
