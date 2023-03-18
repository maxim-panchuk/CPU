import json
from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
    PUSH = 'PUSH'
    DROP = 'DROP'

    PLUS = 'PLUS'
    MOD = 'MOD'
    LT = 'LT'
    NEG = 'NEG'
    INVERT = 'INVERT'

    DUP = 'DUP'
    OVER = 'OVER'
    SWAP = 'SWAP'
    ROT = 'ROT'

    JMP = 'JMP'
    JNT = 'JNT'

    BEGIN = 'BEGIN'
    NOP = 'NOP'

    IF = 'IF'
    ELSE = 'ELSE'
    ENDIF = 'ENDIF'

    READ_OUT = 'READ_OUT'
    WRITE_OUT = 'WRITE_OUT'
    READ_NDR = 'READ_NDR'

    HALT = 'HALT'

    INTERRUPT = 'INTERRUPT'
    INTERRUPT_END = 'INTERRUPT_END'


class Term(namedtuple('Term', 'line_num com arg')):
    """Описание выражения из исходного текста программы."""


def write_code(compiled_code_filename, compiled_code, static_data, static_data_file):
    """Записать машинный код в файл."""
    with open(compiled_code_filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(compiled_code, indent=4))

    with open(static_data_file, "w", encoding='utf-8') as file:
        file.write(json.dumps(static_data, indent=4))


def read_code(compiled_code_file, static_data_file):
    """Прочесть машинный код из файла."""
    with open(compiled_code_file, encoding="utf-8") as file:
        compiled_code = json.loads(file.read())

    for instr in compiled_code:
        # Конвертация строки в Opcode
        instr['opcode'] = Opcode(instr['opcode'])
        # Конвертация списка из term в класс Term
        if 'term' in instr:
            instr['term'] = Term(
                instr['term'][0], instr['term'][1], instr['term'][2])

    with open(static_data_file, encoding="utf-8") as file2:
        if static_data_file == "":
            data_section = []
        else:
            data_section = json.loads(file2.read())

    return compiled_code, data_section
