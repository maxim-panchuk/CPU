# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
# pylint: disable=invalid-name
# pylint: disable=line-too-long

from isa import Opcode, write_code, Term
import sys


def check_brackets(terms):
    deep_if = 0
    deep_else = 0
    for term in terms:
        if term.com == "IF":
            deep_if += 1
        if term.com == "ELSE":
            deep_if -= 1
            deep_else += 1
        if term.com == "ENDIF":
            assert deep_if + 1 == deep_else, "Unbalanced brackets!"
            deep_else -= 1
        assert deep_if >= 0 and deep_else >= 0, "Unbalanced brackets!"
    assert deep_if == 0 and deep_else == 0, "Unbalanced brackets!"

    deep_beg = 0
    deep_while = 0
    for term in terms:
        if term.com == "BEGIN":
            deep_beg += 1
        if term.com == "WHILE":
            deep_beg -= 1
            deep_while += 1
        if term.com == "REPEAT":
            assert deep_beg + 1 == deep_while, "Unbalanced brackets!"
            deep_while -= 1
        assert deep_beg >= 0 and deep_while >= 0, "Unbalanced brackets!"
    assert deep_beg == 0 and deep_while == 0, "Unbalanced brackets!"


def is_number(_str):
    try:
        float(_str)
        return True
    except ValueError:
        return False


def translate(file):
    words_dict = {}
    vars_dict = {}

    terms = []
    strings_map = []

    lines = file.readlines()
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        com = line.split(" ", 1)
        if com[0] == "":
            continue

        com[0] = com[0].strip()

        if com[0][-1] == ":" and com[0][-2] == ')' and com[0][0] == '(':
            words_dict[com[0][1:-2]] = len(strings_map)
            for ch in com[1]:
                strings_map.append(ord(ch))
            strings_map.append(ord('\0'))
            continue

        if com[0][-1] == ':':
            if is_number(com[1].upper()):
                vars_dict[com[0].upper()[:-1]] = com[1].upper()
            else:
                vars_dict[com[0].upper()[:-1]] = words_dict[com[1][1:]]
            continue

        if com[0][0] == '\\':
            com[0] = chr(int(com[0][2:]))

        if com[0][-1] == '\n':
            com = com[0][0:-1]

        if com[0].upper() == "PUSH":
            if com[1].upper() in vars_dict:
                terms.append(Term(line_num, "PUSH", vars_dict[com[1].upper()]))
            else:
                terms.append(Term(line_num, "PUSH", com[1]))
        if com[0].upper() == "PLUS":
            terms.append(Term(line_num, "PLUS", None))
        if com[0].upper() == "DROP":
            terms.append(Term(line_num, "DROP", None))
        if com[0].upper() == "MOD":
            terms.append(Term(line_num, "MOD", None))
        if com[0].upper() == "LT":
            terms.append(Term(line_num, "LT", None))
        if com[0].upper() == "NEG":
            terms.append(Term(line_num, "NEG", None))
        if com[0].upper() == "INVERT":
            terms.append(Term(line_num, "INVERT", None))
        if com[0].upper() == "DUP":
            terms.append(Term(line_num, "DUP", None))
        if com[0].upper() == "OVER":
            terms.append(Term(line_num, "OVER", None))
        if com[0].upper() == "ROT":
            terms.append(Term(line_num, "ROT", None))
        if com[0].upper() == "BEGIN":
            terms.append(Term(line_num, "BEGIN", None))
        if com[0].upper() == "WHILE":
            terms.append(Term(line_num, "WHILE", None))
        if com[0].upper() == "REPEAT":
            terms.append(Term(line_num, "REPEAT", None))
        if com[0].upper() == "IF":
            terms.append(Term(line_num, "IF", None))
        if com[0].upper() == "ELSE":
            terms.append(Term(line_num, "ELSE", None))
        if com[0].upper() == "ENDIF":
            terms.append(Term(line_num, "ENDIF", None))
        if com[0].upper() == "READ":
            terms.append(Term(line_num, "READ_OUT", None))
        if com[0].upper() == "WRITE":
            terms.append(Term(line_num, "WRITE_OUT", None))
        if com[0].upper() == "READ_NDR":
            terms.append(Term(line_num, "READ_NDR", None))
        if com[0].upper() == "WRITE_NDR":
            terms.append(Term(line_num, "WRITE_NDR", None))
        if com[0].upper() == "INTERRUPT":
            terms.append(Term(line_num, "INTERRUPT", None))
        if com[0].upper() == "INTERRUPT_END":
            terms.append(Term(line_num, "INTERRUPT_END", None))
        if com[0].upper() == "READ_OUT":
            terms.append(Term(line_num, "READ_OUT", None))
        if com[0].upper() == "WRITE_OUT":
            terms.append(Term(line_num, "WRITE_OUT", None))
        if com[0].upper() == "SWAP":
            terms.append(Term(line_num, "SWAP", None))

    check_brackets(terms)

    code = []
    stack = []

    for i, term in enumerate(terms):
        if term.com.upper() == "INTERRUPT":
            code.append(None)
            stack.append(i)
            continue

        if term.com.upper() == "INTERRUPT_END":
            inter_begin = stack.pop()
            jmp_skipping_inter = {"opcode": Opcode.JMP.value, "arg": i + 1,
                                  "term": Term(0, "JMP", i + 1)}
            code[inter_begin] = jmp_skipping_inter

            interrupt_end_command = {"opcode": Opcode.INTERRUPT_END.value, "term": term}
            code.append(interrupt_end_command)
            continue

        if term.com.upper() == "IF":
            code.append(None)
            stack.append(i)

        elif term.com.upper() == "ELSE":
            code.append(None)
            stack.append(i)

        elif term.com.upper() == "ENDIF":
            else_i = stack.pop()
            if_i = stack.pop()

            jmp_skipping_then = {"opcode": Opcode.JNT.value, "arg": else_i + 1, "term": terms[if_i]}
            jmp_skipping_else = {"opcode": Opcode.JMP.value, "arg": i + 1, "term": terms[else_i]}

            code[if_i] = jmp_skipping_then
            code[else_i] = jmp_skipping_else
            code.append({"opcode": Opcode.NOP.value, "term": term})

        elif term.com.upper() == "BEGIN":
            code.append(None)
            stack.append(i)

        elif term.com.upper() == "WHILE":
            code.append(None)
            stack.append(i)

        elif term.com.upper() == "REPEAT":
            i_while = stack.pop()
            i_begin = stack.pop()

            jmp_to_begin = {"opcode": Opcode.JMP.value, "arg": i_begin + 1, "term": term}
            jmp_skipping_while = {"opcode": Opcode.JNT.value, "arg": i + 1, "term": terms[i_while]}

            code[i_begin] = {"opcode": Opcode.BEGIN.value, "term": terms[i_begin]}
            code[i_while] = jmp_skipping_while
            code.append(jmp_to_begin)

        else:
            if term.arg is None:
                code.append({"opcode": term.com, "term": term})
            else:
                code.append({"opcode": term.com, "arg": term.arg, "term": term})

    code.append({"opcode": Opcode.HALT.value, "term": Term(len(code) + 1, "HALT", None)})
    return strings_map, code, len(lines)


def main(args):
    assert len(args) == 3, \
        "Wrong arguments: translator.py <user_code_file> <compiled_code_target_file> <static_data_file>"

    source_code_file, compiled_code_file, static_data_file = args

    with open(source_code_file, "rt", encoding="utf-8") as f:
        static_data, compiled_code, loc = translate(f)

    print("source LoC:", loc, "code instr:", len(compiled_code))
    write_code(compiled_code_file, compiled_code, static_data, static_data_file)


if __name__ == "__main__":
    main(sys.argv[1:])
