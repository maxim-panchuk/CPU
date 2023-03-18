# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=no-self-use

"""Интеграционные тесты транслятора и машины
"""

import unittest

import isa
import translator


def start(source_code, compiled_code, correct_compiled_code, static_data):
    translator.main([source_code, compiled_code, static_data])
    result = isa.read_code(compiled_code, static_data)
    correct_code = isa.read_code(correct_compiled_code, static_data)
    assert result == correct_code


class TestTranslator(unittest.TestCase):
    def test_fib(self):
        start("example/translator/source_code", "example/translator/compiled_code",
              "example/translator/compiled_code_correct", "example/translator/static_data")
