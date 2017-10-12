import car_server
import unittest


class server_tests(unittest.TestCase):

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


    ch = car_server.CommandHandler()
    def test_escape_buffer(self):
        test_count = len(self.esc_inputs)
        for i in range(test_count):
            self.assertEqual(
                self.ch.escape_buffer(
                    buf=self.esc_inputs[i]), self.esc_results[i])

    def test_unescape_buffer(self):

        test_count = len(self.esc_inputs)
        for i in range(test_count):
            self.assertEqual(
                self.ch.unescape_buffer(
                    buf=self.esc_results[i]), self.esc_inputs[i])

    def test_escape_loop(self):
        for d in self.random_data:
            forward = self.ch.escape_buffer(d)
            backward = self.ch.unescape_buffer(forward)
            self.assertEqual(d, backward)
        for d in self.esc_inputs:
            forward = self.ch.escape_buffer(d)
            backward = self.ch.unescape_buffer(forward)
            self.assertEqual(d, backward)
        for d in self.esc_results:
            forward = self.ch.escape_buffer(d)
            backward = self.ch.unescape_buffer(forward)
            self.assertEqual(d, backward)


if __name__ == '__main__':
    unittest.main()
