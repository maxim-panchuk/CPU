import json
import logging
import sys
from typing import List
from isa import Opcode, read_code


class Memory:
    """
        Command/Data Memory
        Addresses:
            0-127           --- data memory
            128-memory_size --- program memory

                  0 -> +-------------------+
                       |                   |
                       |                   |
                       |    DATA MEMORY    |
                       |                   |
                       |                   |
                127 -> +-------------------+
                       |                   |
                       |    INSTR. MEM.    |
                       |                   |
        memory_size -> +-------------------+


             INPUT  -> +-------------------+
                       |                   |
            OUTPUT  -> +------ I/O --------+
                       |                   |
                       +-------------------+
    """

    def __init__(self, memory_size, program, io_size, data_section):
        assert memory_size > 0, \
            "Memory size should be more than zero!"
        assert memory_size > len(program) + 128, \
            "Memory size should consist of program and extra 128 bytes for data"
        assert io_size >= 2, \
            "IO memory should contain two pointers, on input and output"
        self.data_address = 0
        self.memory_size = memory_size
        self.data: int | dict = data_section + [0] * (memory_size - len(program) - len(data_section)) + program
        self.program_start = memory_size - len(program)
        self.program_len = len(program)
        self.io = [0] * io_size
        self.io_size = io_size
        self.input_address = 0
        self.output_address = int(io_size / 2)
        self.output_buffer = []

    def latch_data_address(self, val):
        assert 0 <= val <= self.memory_size, \
            f'data_address must be in [0;{self.memory_size}]'
        self.data_address = val

    def get_instruction(self, pc):
        pc += self.program_start
        assert 128 <= pc <= self.memory_size, \
            "PC is out of program memory"
        return self.data[pc]

    def read(self):
        return self.data[self.data_address]

    def write(self, value):
        self.data[self.data_address] = value

    def write_out(self, value):
        assert 0 < self.output_address < self.io_size, \
            "output pointer should be less than io size"

        self.io[self.output_address] = value

        if 0 <= value <= 127:
            value = chr(value)

        value = str(value)
        logging.info('output: %s << %s', ','.join(self.output_buffer), value)
        self.output_buffer.append(value)

    def read_out(self):
        return self.io[self.input_address]


class DataPath:
    def __init__(self, memory_size: int, memory: Memory):
        assert memory_size > 0, \
            "Memory size should be more than zero!"
        self.stack: List[int] = [0] * memory_size
        self.head: int = 0
        self.memory_size: int = memory_size
        self.memory = memory
        self.alu = 0

    def get_tos(self, offset):
        assert 0 <= offset <= 3, \
            "You have access to top 3 elements of stack"
        assert offset < self.head, \
            "Trying to get non-existing element"
        return self.stack[self.head - offset - 1]

    def latch_head(self, sel_val):
        assert sel_val in {-3, -2, -1, 1}, \
            "You can't change the head in increments of 0"
        self.head += sel_val
        assert 0 <= self.head < self.memory_size, \
            f'out of memory: {self.head}'

    def push(self, val):
        self.stack[self.head] = val
        self.latch_head(1)

    def is_true(self):
        res = (0, -1)[self.get_tos(0) == -1]
        self.latch_head(-1)
        return res

    def latch_alu(self, operation):
        if operation == Opcode.PLUS.value:
            self.alu = int(self.get_tos(1) + int(self.get_tos(0)))

        if operation == Opcode.MOD.value:
            self.alu = int(self.get_tos(1) % int(self.get_tos(0)))

        if operation == Opcode.LT.value:
            self.alu = (0, -1)[int(self.get_tos(1)) < int(self.get_tos(0))]  # -1 Если второе число в стеке меньше

        if operation == Opcode.NEG.value:
            self.alu = int(self.get_tos(0)) * (-1)

        if operation == Opcode.INVERT.value:
            self.alu = (int(self.get_tos(0)) + 1) * (-1)

        if operation == Opcode.JNT.value:
            self.alu = (0, -1)[int(self.get_tos(0)) == -1]


class ControlUnit:
    def __init__(self, data_path: DataPath, memory: Memory):
        self.data_path: DataPath = data_path
        self.memory: Memory = memory
        self.pc = 0
        self._tick = 0
        self.is_ready = 1
        self.interrupt = 0
        self.context = 0

    def tick(self):
        self._tick += 1

    def curr_tick(self):
        return self._tick

    def latch_pc(self, select_next: bool = True):
        if select_next:
            self.pc += 1
        else:
            instr = self.memory.get_instruction(self.pc)
            assert instr["opcode"].value in {
                Opcode.JMP.value,
                Opcode.JNT.value
            }, f"instruction must have an argument: {instr}"
            assert 'arg' in instr, "internal error"
            self.pc = instr["arg"]

    def save_context(self):
        self.context = self.pc

    def backup_context(self):
        self.pc = self.context

    def ready(self):
        self.is_ready = 1

    def unready(self):
        self.is_ready = 0

    def do_interrupt(self):
        if self.is_ready == 0:
            return

        if self.interrupt == 0:
            return

        self.unready()
        self.save_context()
        self.pc = 1

    def run(self):
        self.do_interrupt()
        logging.debug('%s', self)
        instr = self.memory.get_instruction(self.pc)
        opcode = instr["opcode"]

        if opcode == Opcode.HALT:
            raise StopIteration()

        if opcode == Opcode.INTERRUPT_END:
            self.ready()
            self.interrupt = 0
            self.backup_context()
            self.tick()

        if opcode == Opcode.PUSH:
            arg = int(instr["arg"])
            self.data_path.push(arg)
            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.PLUS:
            self.data_path.latch_alu(opcode)
            self.data_path.latch_head(-2)
            self.tick()

            self.data_path.push(self.data_path.alu)
            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.MOD:
            self.data_path.latch_alu(opcode)
            self.data_path.latch_head(-2)
            self.tick()

            self.data_path.push(self.data_path.alu)
            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.LT:
            self.data_path.latch_alu(opcode)
            self.data_path.latch_head(-2)
            self.tick()

            self.data_path.push(self.data_path.alu)
            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.NEG:
            self.data_path.latch_alu(opcode)
            self.data_path.latch_head(-1)
            self.tick()

            self.data_path.push(self.data_path.alu)
            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.INVERT:
            self.data_path.latch_alu(opcode)
            self.data_path.latch_head(-1)
            self.tick()

            self.data_path.push(self.data_path.alu)
            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.DUP:
            value = self.data_path.get_tos(0)
            self.data_path.push(value)
            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.OVER:
            value = self.data_path.get_tos(1)
            self.data_path.push(value)
            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.SWAP:
            value1 = self.data_path.get_tos(0)
            value2 = self.data_path.get_tos(1)
            self.data_path.latch_head(-2)
            self.data_path.push(value1)
            self.data_path.push(value2)
            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.ROT:
            value1 = self.data_path.get_tos(1)
            value2 = self.data_path.get_tos(0)
            value3 = self.data_path.get_tos(2)

            self.data_path.latch_head(-3)
            self.data_path.push(value1)
            self.data_path.push(value2)
            self.data_path.push(value3)

            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.BEGIN:
            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.NOP:
            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.JMP:
            address = instr["arg"]
            self.pc = address
            self.tick()
            return

        if opcode == Opcode.JNT:
            if self.data_path.is_true():
                self.latch_pc()
            else:
                self.latch_pc(select_next=False)
            self.tick()
            return

        if opcode == Opcode.DROP:
            self.data_path.latch_head(-1)
            self.latch_pc()
            self.tick()
            return

        if opcode == Opcode.WRITE_OUT:
            value = self.data_path.get_tos(0)
            self.memory.write_out(value)
            self.tick()

            self.data_path.latch_head(-1)
            self.latch_pc()
            self.tick()

        if opcode == Opcode.READ_OUT:
            value = self.memory.read_out()  # Прочли значение с порта ввода
            self.tick()

            self.data_path.push(value)  # Положили значение на стек
            self.latch_pc()
            self.tick()

        if opcode == Opcode.READ_NDR:
            address = self.data_path.get_tos(0)  # Взяли адрес на адрес из стека (... 127)
            self.memory.latch_data_address(address)  # Защелкнули этот адрес у памяти
            self.data_path.latch_head(-1)
            self.tick()

            value = self.memory.read()  # Прочли адрес на переменную из памяти
            self.memory.write(value + 1)  # Записали в память адрес на следующий адрес
            self.data_path.push(value)  # Положили на стек адрес на переменную (... 2)
            self.tick()

            address = self.data_path.get_tos(0)  # Взяли адрес на переменную из стека (2)
            self.memory.latch_data_address(address)  # Защелкнули адрес на переменную в памяти
            self.data_path.latch_head(-1)
            self.tick()

            value = self.memory.read()  # Прочли эту переменную
            self.data_path.push(value)  # Положили в стек прочитанное значение
            self.latch_pc()
            self.tick()

    def __repr__(self):
        state = f"{{TICK: {self._tick}, " \
                f"PC: {self.pc}, " \
                f"HEAD: {self.data_path.head}, " \
                f"TOS: {self.data_path.stack[self.data_path.head - 3]}, " \
                f"{self.data_path.stack[self.data_path.head - 2]}, {self.data_path.stack[self.data_path.head - 1]}}} "

        instr = self.memory.get_instruction(self.pc)
        opcode = instr["opcode"]
        arg = instr.get("arg", "")
        term = instr["term"]
        action = f"{opcode} {arg} ('{term.arg}' @ {term.line_num}:{term.com})"
        return f"{state} {action}"


def simulation(program, data_memory_size, limit, data_section, input_buffer):
    memory = Memory(data_memory_size, program, 2, data_section)
    data_path = DataPath(256, memory)
    control_unit = ControlUnit(data_path, memory)

    instr_counter = 0
    try:
        while True:
            if limit <= instr_counter:
                logging.error("Too long execution")
                break

            control_unit.run()
            check_for_interrupt(control_unit, input_buffer)

            instr_counter += 1
    except StopIteration:
        pass
    return instr_counter, control_unit.curr_tick(), memory.output_buffer


def check_for_interrupt(control_unit: ControlUnit, input_buffer):
    tick = control_unit.curr_tick()
    if len(input_buffer) == 0:
        return

    if (tick >= input_buffer[0]["tick"]) and (control_unit.is_ready == 1):
        control_unit.memory.io[control_unit.memory.input_address] = ord(input_buffer.pop(0)["char"])
        control_unit.interrupt = 1


def main(args):
    assert 2 <= len(args) <= 3, "Wrong arguments: machine.py <code_file> <static_data> [ <input_file> | nothing ]"
    if len(args) == 3:
        compiled_code_file, static_data_file, input_file = args
    else:
        compiled_code_file = args[0]
        static_data_file = args[1]
        input_file = ""

    program, data_section = read_code(compiled_code_file, static_data_file)

    if input_file != "":
        with open(input_file, encoding='utf-8') as file:
            input_text = file.read()
            if input_text != "":
                input_list = json.loads(input_text)
            else:
                input_list = []
    else:
        input_list = []

    instr_counter, ticks, output_buffer = simulation(program, 600, 3000, data_section, input_list)
    print("instr_counter: ", instr_counter, "ticks: ", ticks)
    print("output:", ''.join(output_buffer))

    return output_buffer


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
