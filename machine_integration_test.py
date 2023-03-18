import unittest

import translator
import machine


def start(source_code, compiled_code_file, input_file, static_data_file):
    translator.main([source_code, compiled_code_file, static_data_file])
    if input_file == "":
        return machine.main([compiled_code_file, static_data_file])
    return machine.main([compiled_code_file, static_data_file, input_file])


class TestMachine(unittest.TestCase):

    def test_fib(self):
        output = start("example/fib/source_code", "example/fib/compiled_code", "", "example/fib/static_data")
        assert output[0] == '4613732'

    def test_hello(self):
        output = start("example/hello/source_code", "example/hello/compiled_code", "", "example/hello/static_data")
        assert output[0] == 'H' and output[1] == 'e' and output[2] == 'l' \
               and output[3] == 'l' and output[4] == 'o' and output[5] == ' ' \
               and output[6] == 'w' and output[7] == 'o' and output[8] == 'r' \
               and output[9] == 'l' and output[10] == 'd' and output[11] == '!'

    def test_cat(self):
        output = start("example/cat/source_code", "example/cat/compiled_code", "example/cat/input_file",
                       "example/cat/static_data")
        assert output[0] == 'h' and output[1] == 'e' and output[2] == 'l' \
               and output[3] == 'l' and output[4] == 'o'

    def test_if(self):
        output = start("example/if/source_code", "example/if/compiled_code", "", "example/if/static_data")
        assert output[0] == '-1'

    def test_while(self):
        output = start("example/while/source_code", "example/while/compiled_code", "", "example/while/static_data")
        assert output[0] == '-4' and output[1] == '-3' and output[2] == '-2' \
               and output[3] == '-1'
