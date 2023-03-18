 # FORTH. Транслятор и модель
 
- Панчук Максим P33111
- `forth | stack | neum | hw | instr | struct | trap | port | prob2`

## Язык программирования

```ebnf
program ::= term

term ::= command
        | var_init
        | string_init
        | term term

command ::= "PUSH symbol" | "DROP" |
            "PLUS" | "MOD" | "LT" | "NEG" | "INVERT" |
            "DUP" | "OVER" | "SWAP" | "ROT" |
            "BEGIN" | "WHILE" | "REPEAT"
            "IF" | "ELSE" | "ENDIF"
            "READ_OUT" | "WRITE_OUT" | "READ_NDR"
            "INTERRUPT" | "INTERRUPT_END"
            "HALT"
            
symbol = [-2^31; 2^31], ["a"; "z"]

string_init = (string_name): string_value

var_init ::= var_name: var_value 
                | &string_name
```

Код выполняется последовательно. Операции:

- `PUSH push_symbol` -- `...a` >> `...a pushued simbol` -- Кладет символ на стек
- `DROP` -- `...a b` >> `...a`
- `PLUS` -- `...a b` >> `...[a + b]`
- `MOD` -- `...a b` >> `...[a % b]`
- `LT` -- `...a b` >> `...[a < b ? -1 : 0]`
- `NEG` -- `...a` >> `...[a * (-1)`
- `INVERT` -- `...a` >> `...[(a + 1) * (-1)]`
- `DUP` -- `...a` >> `...a a`
- `OVER` -- `...a b` >> `...a b a`
- `SWAP` -- `...a b` >> `...b a`
- `ROT` -- `...a b c` >> `...b c a`
- `BEGIN` -- Если при WHILE было true, тогда вернется на BEGIN.
- `WHILE` -- Возьмет со стека значение, если оно true - перейдет далее иначе - на одну команду дальше REPEAT.
- `REPEAT` -- Возвращает на одну команду дальше BEGIN.
- `IF` -- Возьмет со стека значение, если оно true - перейдет далее, иначе - на ELSE.
- `ELSE` -- В этот блок кода заходим, если IF адресовал на него.
- `ENDIF` -- Закрывает блок кода IF.
- `READ_OUT` -- Читает с порта ввода внешнего устройства.
- `WRITE_OUT` -- Пишет в порт вывода для внешнего устройства.
- `READ_NDR` -- Обращается по адресу, который указывает на адрес значения. Указатель на адрес инкрементирует после прочтения.
- `INTERRUPT` -- Объявляет начло блока кода для обработки прерывания.
- `INTERRUPT_END` -- Конец блока кода для обработки прерывания.


## Организация памяти
Модель памяти процессора:

1. Память команд. Машинное слово -- не определено. Реализуется списком словарей, описывающих инструкции (одно слово -- одна ячейка).
2. Память данных. Машинное слово -- 32 бита, знаковое. Линейное адресное пространство. Реализуется списком чисел.
3. Стек. Заменяет регистры. Машинное слово -- 32 бита, знаковое. Линейное адресное пространство. Реализуется списком чисел.
4. Порты ввода-вывода. Машинное слово -- 32 бита, знаковое. Линейное адресное пространство. Реализуется списком чисел.

Строки, объявленные пользователем распределяются по памяти один символ на ячейку.

```text
Instruction memory
+-----------------------------+
| 00  : jmp N                 |
| 01  : interrupt handler     |
|    ...                      | 
| n   : program start         |
|    ...                      |
+-----------------------------+

Data memory
+-----------------------------+
| 00  : data                  |
|                             |
|                             |
|    ...                      |
| 127 : data                  |
| 127 : program               |
| 128 : program               |
|    ...                      |
+-----------------------------+

Ports
+-----------------------------+
| 00  : input data            |
|    ...                      |
| n/2 : input_data            |
+-----------------------------+
| n/2 + 1  : output data      |     
|         ...                 |
| n        : output_data      |
+-----------------------------+
```

## Система команд

Особенности процессора:

- Машинное слово -- 32 бит, знаковое.
- `Память`:
    - адресуется через регистр `data_address`;
    - может быть записана:
        - с порта ввода;
        - с верхушки стека;
    - может быть прочитана:
        - в буффер;
- `Стек`:
    - адресуется через регистр `data_head`;
    - Верхушка стека (верхние 3 элемента):
        - может быть записана:
            - из буфера;
        - может быть прочитана:
            - на вход АЛУ
            - на вывод
        - используется как флаг `is_true` 1 - на верхушке `True`, иначе `False`
- Ввод-вывод -- port-mapped, по прерыванию.
- `program_counter` -- счётчик команд:
    - инкрементируется после каждой инструкции или перезаписывается инструкцией перехода.
- `ready` - флаг готовности:
    - 0 - если процессор должен обработать входящее прерывание, 1 - процессор не может обработать входящее прерывание/входящих прерываний нет
- `interrupt` - обрабатывается ли на данный момент прерывание.

### Набор инструкции

| Syntax          | Mnemonic         | Кол-во тактов | Comment  |
|:----------------|:-----------------|---------------|:---------|
| `PUSH {symbol}` | PUSH {symbol}    | 1             | --       |
| `DROP`          | DROP             | 1             | --       |
| `PLUS`          | PLUS             | 2             | --       |
| `MOD`           | MOD              | 2             | --       |
| `NEGATE`        | NEG              | 2             | --       |
| `INVERT`        | INV              | 2             | --       |
| `LT`            | LT               | 2             | --       |
| `DUP`           | DUP              | 1             | --       |
| `OVER`          | OVER             | 1             | --       |
| `SWAP`          | SWAP             | 1             | --       |
| `ROT`           | ROT              | 1             | --       |
| `INTERRUPT`     | JMP {INTEND + 1} | 1             | --       |
| `INTERRUPT_END` | INTEND           | 1             | --       |
| `IF`            | JNT {ELSE + 1}   | 1             | --       |
| `ELSE`          | JMP {ENDIF}      | 1             | --       |
| `ENDIF`         | NOP              | 1             | --       |
| `BEGIN`         | BEGIN            | 1             | --       |
| `WHILE`         | JNT {REPEAT + 1} | 1             | --       |
| `REPEAT`        | JMP {BEGIN + 1}  | 1             | --       |
| `NOP`           | NOP              | 1             | --       |
| `READ_OUT`      | READ_OUT         | 2             | --       |
| `WRITE_OUT`     | WRITE_OUT        | 2             | --       |
| `READ_NDR`      | READ_NDR         | 4             | --       |

### Кодирование инструкций

- Машинный код сериализуется в список JSON.
- Один элемент списка, одна инструкция.
- Индекс списка -- адрес инструкции. Используется для команд перехода.

Пример:

```json
[
   {
        "opcode": "PUSH",
        "arg": "0",
        "term": [
            1,
            "PUSH",
            "0"
        ]
    }
]
```

- `opcode` -- строка с кодом операции;
- `arg` -- аргумент (может отсутствовать);
- `term` -- информация о связанном месте в исходном коде (если есть).

Типы данные в модуле [isa](./isa.py), где:

- `Opcode` -- перечисление кодов операций;
- `Term` -- структура для описания значимого фрагмента кода исходной программы.


## Транслятор

Интерфейс командной строки: `translator.py <source_code> <compiled_code> <static_data>"`

Реализовано в модуле: [translator](./translator.py)

Этапы трансляции (функция `translate`):
1. Трансформирование текста в последовательность значимых термов.
    - Переменные:
        - Транслируются в соответствующие значения на этапе трансляции.
        - Задаётся либо числовым значением, либо указателем на начало строки (используя &string_name)
2. Проверка корректности программы (одинаковое количество IF, ELSE, ENDIF и BEGIN, WHILE, REPEAT).
3. Генерация машинного кода.

Правила генерации машинного кода:

- одно слово языка -- одна инструкция;
- для команд, однозначно соответствующих инструкциям -- прямое отображение;
- для циклов с соблюдением парности (многоточие -- произвольный код):

| Номер команды/инструкции | Программа | Машинный код |
|:-------------------------|:----------|:-------------|
| n                        | `BEGIN`   | `BEGIN`      |
| ...                      | ...       | ...          |
| n+3                      | `WHILE`   | `JNT (k+1)`  |
| ...                      | ...       | ...          |
| k                        | `REPEAT`  |  `JMP (n+1)` |
| k+1                      | ...       | ...          |

- для условных операторов (многоточие -- произвольный код):

| Номер команды/инструкции | Программа | Машинный код |
|:-------------------------|:----------|:-------------|
| n                        | `IF`      | `JNT (n+4)`  |
| ...                      | ...       | ...          |
| n+3                      | `ELSE`    | `JMP (k+1)`  |
| ...                      | ...       | ...          |
| k                        | `ENDIF`   | `NOP`        |
| k+1                      | ...       | ...          |

- для обработчиков прерываний:

| Номер команды/инструкции | Программа         | Машинный код |
|:-------------------------|:------------------|:-------------|
| 0                        | `JMP`             | `JMP n`      |
| 1                        | `INTERRUPT PROG`  | ...          |
| ...                      | ...               | ...          |
| n-1                      | `INTERRUPT END`   | `INTEND`     |
| n                        | `MAIN PROG`       |  `...`       |
| ...                      | ...               | ...          |

## Модель процессора

Реализовано в модуле: [machine](./machine.py).

- `latch` - защелкнуть значение `data_address`
- `PC` - program counter
- `read_out` - прочесть с порта ввода
- `write_out` - записать в порт вывода
- `signal` - `get_tos`, `push`, `is_true`, `latch_alu`

        

        +-----------+                     +----------+
        | Data Path |--------latch------->| Data Adr |--------+
        +-----------+                     +----------+        |
         ^     ^   ^                                          |
         |     |   |                      +----------+        |
       signal arg  |                      |          |        |
         |     |   +--------data--------- |  Data    |<-------+
         |     |                          |  Mem.    |
        +-----------+                     |          |
        | Control U |                     +----------+
        +-----------+                     +----------+
         ^       ^                         |          |
         |       |                         |  Progr.  |
         |       +-----------instr---------|  Mem.    |
         |       |                         |          |
         |       +-------------PC--------->+----------+
         |
         |                                 +----------+
         |------------read_out-- ----------| In Port  |
         |                                 +----------+
         |                                 | Out Port |
         +------------write_out----------->+----------+

### Data Path

                  latch
                    |
                    |
             +-------------+
      +----->|  data_head  |---------------+                     +----------+
      |      +-------------+     |         |                     |          |<------ push
      |                          |         |                     |          |<------ get_tos
      |                          |         |                     |Data stack|
      |                          |     data_head                 |          |
    +---------+<-----(+1)--------+         |                     |          | 
    |         |<-----(-1)--------+         |                     +----------+
    |   MUX   |<-----(-2)--------+         |                     |          |
    |         |<-----(-3)--------+         +-------------------->|   TOS    |<--------+
    +---------+                                                  |          |         |
         ^                                                       +----------+         |
        sel                                                        |   |              |
                                          <-------is_true----------+   |              |
              +-----+                                                  |              |
              |     |<-----------------------------------data_tos------+              |
    wr_out<---| MUX |                       |       |                                 |
              |     |                     arg1    arg2                               push
              +-----+                       |       |                                 |
                ^                      +------------------+                           |
                |                      |                  |                           |
               sel                     |       ALU        |<--- run                   |
                                       |                  |                           |
                                       +------------------+                  +----------------+
                                                   |                         |                |
                                                   |                         |      MUX       |<----- sel
                                                   |                         |                |
                                                   |                         +----------------+
                                                   |                          ^      ^       ^
                                                   |                          |      |       |
                                                   |                          |      |       |
                                                   +--------------------------+      |       |
                                                                                    arg    input

Сигналы (обрабатываются за один такт, реализованы в виде методов класса):

- `push` -- записать на макушку стека значение из АЛУ, input или argument
- `get_tos` -- прочитать из макушки стека
- `latch` -- защёлкнуть значение в `data_head`
- `run` -- сигнал АЛУ для вычислений. Из стека оно берет два значения

Флаги:

- `is_true` -- лежит ли на стеке true.


### АЛУ

                       +----------------------+
                       |                      |
    operation_sel----->|      OPERATION       |------------>
                       |                      |
                       +----------------------+
                             ^         ^
                             |         |
                             |         |
                           l_val      r_val

Сигналы (обрабатываются за один такт, реализованы в виде методов класса):

- `operation_sel` -- произвести операцию

### Control Unit



        


                        +---------------------------jmp_addr-------------------------+
                        |                                                            |
                        +---------------------------sel_next------------------------ |
                        |                                                            |
            +----------------+                                             +--------------------+
            |                |-----signal---->                      sel--->|                    |
            | Instr. Decoder |----- arg------>                             |        MUX         |<-------+
            |                |                                             |                    |        |
            +----------------+                                             +--------------------+        |
                    ^                                                                |                   |
                    |                                                                |                  (+1)
                    |                                                                |                   |
                instruction                                                          |                   |
                                                                           +--------------------+        |
                                                                           |                    |+-------+
                                                                           |         PC         |
                              on/off               yes/no                  |                    |-------+                          
                                |                    |                     +--------------------+       |
                          +----------+          +----------+                         |      ^           |
                          |          |          |          |                         |      |       +---------+
                          |  ready   |--->      |interrupt |---->                    PC     |       |         |
                          |          |          |          |                         |      +-------| CONTEXT |<----- latch
                          +----------+          +----------+                                        |         |
                                                                                                    +---------+

Реализован в классе `control_unit`.

- Hardwired (реализовано полностью на python).
- Моделирование на уровне инструкций.
- Трансляция инструкции в последовательность (0-3 тактов) сигналов: `run`.

Сигнал:

- `latch_program_couter` -- сигнал для обновления счётчика команд в control_unit.
- `on/off` -- переключить тумблер ready (либо 0, либо 1).
- `latch_context` -- сигнал для защёлкивания значения context.
- `y/n` -- переключить значение interrupt (либо 0, либо 1).

Особенности работы модели:

- Для журнала состояний процессора используется стандартный модуль logging.
- Количество инструкций для моделирования ограничено hardcoded константой.
- Остановка моделирования осуществляется при помощи исключений:
    - `EOFError` -- если нет данных для чтения из порта ввода-вывода;
    - `StopIteration` -- если выполнена инструкция `halt`.
- Управление симуляцией реализовано в функции `simulate`.

## Аппробация

В качестве тестов для `machine` использовались 5 тестов:

1. [hello](example/hello/source_code) - Выводит в консоль `Hello world!`.
2. [cat](example/cat/source_code) - Выводим в консоль то, что пришло извне.
3. [prob2](example/fib/source_code) - Вторая проблема Эйлера.
4. [if](example/if/source_code) - Проверка корректности работы `IF`
5. [while](example/while/source_code) - Проверка корректности работы `WHILE`

Интеграционный тест: [machine_integration_test](./machine_integration_test.py)

В качестве тестов для `translator`

1. [prob2](example/fib/source_code)

Интеграционный тест: [translator_integration_test](./translator_integration_test.py)

CI:

``` yaml
lab3-example:
  stage: test
  image:
    name: python-tools
    entrypoint: [""]
  script:
    - python3-coverage run -m pytest --verbose
    - find . -type f -name "*.py" | xargs -t python3-coverage report
    - find . -type f -name "*.py" | xargs -t pep8 --ignore=E501
    - find . -type f -name "*.py" | xargs -t pylint
```

где:

- `python3-coverage` -- формирование отчёта об уровне покрытия исходного кода.
- `pytest` -- утилита для запуска тестов.
- `pep8` -- утилита для проверки форматирования кода. `E501` (длина строк) отключено, но не следует этим злоупотреблять.
- `pylint` -- утилита для проверки качества кода. Некоторые правила отключены в отдельных модулях с целью упрощения кода.

Пример использования и журнал работы процессора на примере `cat`:

```console
python machine.py example/fib/compiled_code example/fib/static_data
DEBUG:root:{TICK: 0, PC: 0, HEAD: 0, TOS: 0, 0, 0}  PUSH 0 ('0' @ 1:PUSH)
DEBUG:root:{TICK: 1, PC: 1, HEAD: 1, TOS: 0, 0, 0}  PUSH 1 ('1' @ 2:PUSH)
DEBUG:root:{TICK: 2, PC: 2, HEAD: 2, TOS: 0, 0, 1}  PUSH 2 ('2' @ 3:PUSH)
DEBUG:root:{TICK: 3, PC: 3, HEAD: 3, TOS: 0, 1, 2}  BEGIN  ('None' @ 4:BEGIN)
DEBUG:root:{TICK: 4, PC: 4, HEAD: 3, TOS: 0, 1, 2}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 5, PC: 5, HEAD: 4, TOS: 1, 2, 2}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 6, PC: 6, HEAD: 5, TOS: 2, 2, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 8, PC: 7, HEAD: 4, TOS: 1, 2, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 9, PC: 8, HEAD: 3, TOS: 0, 1, 2}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 10, PC: 9, HEAD: 4, TOS: 1, 2, 2}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 11, PC: 10, HEAD: 5, TOS: 2, 2, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 13, PC: 11, HEAD: 4, TOS: 1, 2, 0}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 15, PC: 12, HEAD: 4, TOS: 1, 2, -1}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 16, PC: 13, HEAD: 3, TOS: 0, 1, 2}  ROT  ('None' @ 14:ROT)
DEBUG:root:{TICK: 17, PC: 14, HEAD: 3, TOS: 1, 2, 0}  OVER  ('None' @ 15:OVER)
DEBUG:root:{TICK: 18, PC: 15, HEAD: 4, TOS: 2, 0, 2}  PLUS  ('None' @ 16:PLUS)
DEBUG:root:{TICK: 20, PC: 16, HEAD: 3, TOS: 1, 2, 2}  SWAP  ('None' @ 17:SWAP)
DEBUG:root:{TICK: 21, PC: 17, HEAD: 3, TOS: 1, 2, 2}  ROT  ('None' @ 18:ROT)
DEBUG:root:{TICK: 22, PC: 18, HEAD: 3, TOS: 2, 2, 1}  OVER  ('None' @ 19:OVER)
DEBUG:root:{TICK: 23, PC: 19, HEAD: 4, TOS: 2, 1, 2}  OVER  ('None' @ 20:OVER)
DEBUG:root:{TICK: 24, PC: 20, HEAD: 5, TOS: 1, 2, 1}  PLUS  ('None' @ 21:PLUS)
DEBUG:root:{TICK: 26, PC: 21, HEAD: 4, TOS: 2, 1, 3}  SWAP  ('None' @ 22:SWAP)
DEBUG:root:{TICK: 27, PC: 22, HEAD: 4, TOS: 2, 3, 1}  DROP  ('None' @ 23:DROP)
DEBUG:root:{TICK: 28, PC: 23, HEAD: 3, TOS: 2, 2, 3}  JMP 31 ('None' @ 24:ELSE)
DEBUG:root:{TICK: 29, PC: 31, HEAD: 3, TOS: 2, 2, 3}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 30, PC: 4, HEAD: 3, TOS: 2, 2, 3}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 31, PC: 5, HEAD: 4, TOS: 2, 3, 3}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 32, PC: 6, HEAD: 5, TOS: 3, 3, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 34, PC: 7, HEAD: 4, TOS: 2, 3, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 35, PC: 8, HEAD: 3, TOS: 2, 2, 3}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 36, PC: 9, HEAD: 4, TOS: 2, 3, 3}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 37, PC: 10, HEAD: 5, TOS: 3, 3, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 39, PC: 11, HEAD: 4, TOS: 2, 3, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 41, PC: 12, HEAD: 4, TOS: 2, 3, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 42, PC: 24, HEAD: 3, TOS: 2, 2, 3}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 43, PC: 25, HEAD: 3, TOS: 2, 3, 2}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 44, PC: 26, HEAD: 4, TOS: 3, 2, 3}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 45, PC: 27, HEAD: 5, TOS: 2, 3, 2}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 47, PC: 28, HEAD: 4, TOS: 3, 2, 5}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 48, PC: 29, HEAD: 4, TOS: 3, 5, 2}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 49, PC: 30, HEAD: 3, TOS: 2, 3, 5}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 50, PC: 31, HEAD: 3, TOS: 2, 3, 5}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 51, PC: 4, HEAD: 3, TOS: 2, 3, 5}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 52, PC: 5, HEAD: 4, TOS: 3, 5, 5}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 53, PC: 6, HEAD: 5, TOS: 5, 5, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 55, PC: 7, HEAD: 4, TOS: 3, 5, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 56, PC: 8, HEAD: 3, TOS: 2, 3, 5}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 57, PC: 9, HEAD: 4, TOS: 3, 5, 5}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 58, PC: 10, HEAD: 5, TOS: 5, 5, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 60, PC: 11, HEAD: 4, TOS: 3, 5, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 62, PC: 12, HEAD: 4, TOS: 3, 5, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 63, PC: 24, HEAD: 3, TOS: 2, 3, 5}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 64, PC: 25, HEAD: 3, TOS: 2, 5, 3}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 65, PC: 26, HEAD: 4, TOS: 5, 3, 5}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 66, PC: 27, HEAD: 5, TOS: 3, 5, 3}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 68, PC: 28, HEAD: 4, TOS: 5, 3, 8}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 69, PC: 29, HEAD: 4, TOS: 5, 8, 3}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 70, PC: 30, HEAD: 3, TOS: 2, 5, 8}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 71, PC: 31, HEAD: 3, TOS: 2, 5, 8}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 72, PC: 4, HEAD: 3, TOS: 2, 5, 8}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 73, PC: 5, HEAD: 4, TOS: 5, 8, 8}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 74, PC: 6, HEAD: 5, TOS: 8, 8, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 76, PC: 7, HEAD: 4, TOS: 5, 8, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 77, PC: 8, HEAD: 3, TOS: 2, 5, 8}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 78, PC: 9, HEAD: 4, TOS: 5, 8, 8}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 79, PC: 10, HEAD: 5, TOS: 8, 8, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 81, PC: 11, HEAD: 4, TOS: 5, 8, 0}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 83, PC: 12, HEAD: 4, TOS: 5, 8, -1}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 84, PC: 13, HEAD: 3, TOS: 2, 5, 8}  ROT  ('None' @ 14:ROT)
DEBUG:root:{TICK: 85, PC: 14, HEAD: 3, TOS: 5, 8, 2}  OVER  ('None' @ 15:OVER)
DEBUG:root:{TICK: 86, PC: 15, HEAD: 4, TOS: 8, 2, 8}  PLUS  ('None' @ 16:PLUS)
DEBUG:root:{TICK: 88, PC: 16, HEAD: 3, TOS: 5, 8, 10}  SWAP  ('None' @ 17:SWAP)
DEBUG:root:{TICK: 89, PC: 17, HEAD: 3, TOS: 5, 10, 8}  ROT  ('None' @ 18:ROT)
DEBUG:root:{TICK: 90, PC: 18, HEAD: 3, TOS: 10, 8, 5}  OVER  ('None' @ 19:OVER)
DEBUG:root:{TICK: 91, PC: 19, HEAD: 4, TOS: 8, 5, 8}  OVER  ('None' @ 20:OVER)
DEBUG:root:{TICK: 92, PC: 20, HEAD: 5, TOS: 5, 8, 5}  PLUS  ('None' @ 21:PLUS)
DEBUG:root:{TICK: 94, PC: 21, HEAD: 4, TOS: 8, 5, 13}  SWAP  ('None' @ 22:SWAP)
DEBUG:root:{TICK: 95, PC: 22, HEAD: 4, TOS: 8, 13, 5}  DROP  ('None' @ 23:DROP)
DEBUG:root:{TICK: 96, PC: 23, HEAD: 3, TOS: 10, 8, 13}  JMP 31 ('None' @ 24:ELSE)
DEBUG:root:{TICK: 97, PC: 31, HEAD: 3, TOS: 10, 8, 13}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 98, PC: 4, HEAD: 3, TOS: 10, 8, 13}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 99, PC: 5, HEAD: 4, TOS: 8, 13, 13}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 100, PC: 6, HEAD: 5, TOS: 13, 13, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 102, PC: 7, HEAD: 4, TOS: 8, 13, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 103, PC: 8, HEAD: 3, TOS: 10, 8, 13}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 104, PC: 9, HEAD: 4, TOS: 8, 13, 13}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 105, PC: 10, HEAD: 5, TOS: 13, 13, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 107, PC: 11, HEAD: 4, TOS: 8, 13, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 109, PC: 12, HEAD: 4, TOS: 8, 13, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 110, PC: 24, HEAD: 3, TOS: 10, 8, 13}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 111, PC: 25, HEAD: 3, TOS: 10, 13, 8}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 112, PC: 26, HEAD: 4, TOS: 13, 8, 13}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 113, PC: 27, HEAD: 5, TOS: 8, 13, 8}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 115, PC: 28, HEAD: 4, TOS: 13, 8, 21}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 116, PC: 29, HEAD: 4, TOS: 13, 21, 8}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 117, PC: 30, HEAD: 3, TOS: 10, 13, 21}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 118, PC: 31, HEAD: 3, TOS: 10, 13, 21}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 119, PC: 4, HEAD: 3, TOS: 10, 13, 21}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 120, PC: 5, HEAD: 4, TOS: 13, 21, 21}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 121, PC: 6, HEAD: 5, TOS: 21, 21, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 123, PC: 7, HEAD: 4, TOS: 13, 21, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 124, PC: 8, HEAD: 3, TOS: 10, 13, 21}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 125, PC: 9, HEAD: 4, TOS: 13, 21, 21}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 126, PC: 10, HEAD: 5, TOS: 21, 21, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 128, PC: 11, HEAD: 4, TOS: 13, 21, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 130, PC: 12, HEAD: 4, TOS: 13, 21, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 131, PC: 24, HEAD: 3, TOS: 10, 13, 21}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 132, PC: 25, HEAD: 3, TOS: 10, 21, 13}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 133, PC: 26, HEAD: 4, TOS: 21, 13, 21}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 134, PC: 27, HEAD: 5, TOS: 13, 21, 13}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 136, PC: 28, HEAD: 4, TOS: 21, 13, 34}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 137, PC: 29, HEAD: 4, TOS: 21, 34, 13}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 138, PC: 30, HEAD: 3, TOS: 10, 21, 34}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 139, PC: 31, HEAD: 3, TOS: 10, 21, 34}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 140, PC: 4, HEAD: 3, TOS: 10, 21, 34}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 141, PC: 5, HEAD: 4, TOS: 21, 34, 34}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 142, PC: 6, HEAD: 5, TOS: 34, 34, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 144, PC: 7, HEAD: 4, TOS: 21, 34, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 145, PC: 8, HEAD: 3, TOS: 10, 21, 34}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 146, PC: 9, HEAD: 4, TOS: 21, 34, 34}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 147, PC: 10, HEAD: 5, TOS: 34, 34, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 149, PC: 11, HEAD: 4, TOS: 21, 34, 0}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 151, PC: 12, HEAD: 4, TOS: 21, 34, -1}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 152, PC: 13, HEAD: 3, TOS: 10, 21, 34}  ROT  ('None' @ 14:ROT)
DEBUG:root:{TICK: 153, PC: 14, HEAD: 3, TOS: 21, 34, 10}  OVER  ('None' @ 15:OVER)
DEBUG:root:{TICK: 154, PC: 15, HEAD: 4, TOS: 34, 10, 34}  PLUS  ('None' @ 16:PLUS)
DEBUG:root:{TICK: 156, PC: 16, HEAD: 3, TOS: 21, 34, 44}  SWAP  ('None' @ 17:SWAP)
DEBUG:root:{TICK: 157, PC: 17, HEAD: 3, TOS: 21, 44, 34}  ROT  ('None' @ 18:ROT)
DEBUG:root:{TICK: 158, PC: 18, HEAD: 3, TOS: 44, 34, 21}  OVER  ('None' @ 19:OVER)
DEBUG:root:{TICK: 159, PC: 19, HEAD: 4, TOS: 34, 21, 34}  OVER  ('None' @ 20:OVER)
DEBUG:root:{TICK: 160, PC: 20, HEAD: 5, TOS: 21, 34, 21}  PLUS  ('None' @ 21:PLUS)
DEBUG:root:{TICK: 162, PC: 21, HEAD: 4, TOS: 34, 21, 55}  SWAP  ('None' @ 22:SWAP)
DEBUG:root:{TICK: 163, PC: 22, HEAD: 4, TOS: 34, 55, 21}  DROP  ('None' @ 23:DROP)
DEBUG:root:{TICK: 164, PC: 23, HEAD: 3, TOS: 44, 34, 55}  JMP 31 ('None' @ 24:ELSE)
DEBUG:root:{TICK: 165, PC: 31, HEAD: 3, TOS: 44, 34, 55}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 166, PC: 4, HEAD: 3, TOS: 44, 34, 55}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 167, PC: 5, HEAD: 4, TOS: 34, 55, 55}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 168, PC: 6, HEAD: 5, TOS: 55, 55, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 170, PC: 7, HEAD: 4, TOS: 34, 55, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 171, PC: 8, HEAD: 3, TOS: 44, 34, 55}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 172, PC: 9, HEAD: 4, TOS: 34, 55, 55}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 173, PC: 10, HEAD: 5, TOS: 55, 55, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 175, PC: 11, HEAD: 4, TOS: 34, 55, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 177, PC: 12, HEAD: 4, TOS: 34, 55, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 178, PC: 24, HEAD: 3, TOS: 44, 34, 55}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 179, PC: 25, HEAD: 3, TOS: 44, 55, 34}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 180, PC: 26, HEAD: 4, TOS: 55, 34, 55}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 181, PC: 27, HEAD: 5, TOS: 34, 55, 34}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 183, PC: 28, HEAD: 4, TOS: 55, 34, 89}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 184, PC: 29, HEAD: 4, TOS: 55, 89, 34}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 185, PC: 30, HEAD: 3, TOS: 44, 55, 89}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 186, PC: 31, HEAD: 3, TOS: 44, 55, 89}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 187, PC: 4, HEAD: 3, TOS: 44, 55, 89}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 188, PC: 5, HEAD: 4, TOS: 55, 89, 89}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 189, PC: 6, HEAD: 5, TOS: 89, 89, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 191, PC: 7, HEAD: 4, TOS: 55, 89, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 192, PC: 8, HEAD: 3, TOS: 44, 55, 89}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 193, PC: 9, HEAD: 4, TOS: 55, 89, 89}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 194, PC: 10, HEAD: 5, TOS: 89, 89, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 196, PC: 11, HEAD: 4, TOS: 55, 89, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 198, PC: 12, HEAD: 4, TOS: 55, 89, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 199, PC: 24, HEAD: 3, TOS: 44, 55, 89}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 200, PC: 25, HEAD: 3, TOS: 44, 89, 55}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 201, PC: 26, HEAD: 4, TOS: 89, 55, 89}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 202, PC: 27, HEAD: 5, TOS: 55, 89, 55}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 204, PC: 28, HEAD: 4, TOS: 89, 55, 144}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 205, PC: 29, HEAD: 4, TOS: 89, 144, 55}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 206, PC: 30, HEAD: 3, TOS: 44, 89, 144}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 207, PC: 31, HEAD: 3, TOS: 44, 89, 144}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 208, PC: 4, HEAD: 3, TOS: 44, 89, 144}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 209, PC: 5, HEAD: 4, TOS: 89, 144, 144}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 210, PC: 6, HEAD: 5, TOS: 144, 144, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 212, PC: 7, HEAD: 4, TOS: 89, 144, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 213, PC: 8, HEAD: 3, TOS: 44, 89, 144}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 214, PC: 9, HEAD: 4, TOS: 89, 144, 144}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 215, PC: 10, HEAD: 5, TOS: 144, 144, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 217, PC: 11, HEAD: 4, TOS: 89, 144, 0}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 219, PC: 12, HEAD: 4, TOS: 89, 144, -1}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 220, PC: 13, HEAD: 3, TOS: 44, 89, 144}  ROT  ('None' @ 14:ROT)
DEBUG:root:{TICK: 221, PC: 14, HEAD: 3, TOS: 89, 144, 44}  OVER  ('None' @ 15:OVER)
DEBUG:root:{TICK: 222, PC: 15, HEAD: 4, TOS: 144, 44, 144}  PLUS  ('None' @ 16:PLUS)
DEBUG:root:{TICK: 224, PC: 16, HEAD: 3, TOS: 89, 144, 188}  SWAP  ('None' @ 17:SWAP)
DEBUG:root:{TICK: 225, PC: 17, HEAD: 3, TOS: 89, 188, 144}  ROT  ('None' @ 18:ROT)
DEBUG:root:{TICK: 226, PC: 18, HEAD: 3, TOS: 188, 144, 89}  OVER  ('None' @ 19:OVER)
DEBUG:root:{TICK: 227, PC: 19, HEAD: 4, TOS: 144, 89, 144}  OVER  ('None' @ 20:OVER)
DEBUG:root:{TICK: 228, PC: 20, HEAD: 5, TOS: 89, 144, 89}  PLUS  ('None' @ 21:PLUS)
DEBUG:root:{TICK: 230, PC: 21, HEAD: 4, TOS: 144, 89, 233}  SWAP  ('None' @ 22:SWAP)
DEBUG:root:{TICK: 231, PC: 22, HEAD: 4, TOS: 144, 233, 89}  DROP  ('None' @ 23:DROP)
DEBUG:root:{TICK: 232, PC: 23, HEAD: 3, TOS: 188, 144, 233}  JMP 31 ('None' @ 24:ELSE)
DEBUG:root:{TICK: 233, PC: 31, HEAD: 3, TOS: 188, 144, 233}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 234, PC: 4, HEAD: 3, TOS: 188, 144, 233}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 235, PC: 5, HEAD: 4, TOS: 144, 233, 233}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 236, PC: 6, HEAD: 5, TOS: 233, 233, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 238, PC: 7, HEAD: 4, TOS: 144, 233, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 239, PC: 8, HEAD: 3, TOS: 188, 144, 233}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 240, PC: 9, HEAD: 4, TOS: 144, 233, 233}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 241, PC: 10, HEAD: 5, TOS: 233, 233, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 243, PC: 11, HEAD: 4, TOS: 144, 233, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 245, PC: 12, HEAD: 4, TOS: 144, 233, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 246, PC: 24, HEAD: 3, TOS: 188, 144, 233}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 247, PC: 25, HEAD: 3, TOS: 188, 233, 144}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 248, PC: 26, HEAD: 4, TOS: 233, 144, 233}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 249, PC: 27, HEAD: 5, TOS: 144, 233, 144}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 251, PC: 28, HEAD: 4, TOS: 233, 144, 377}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 252, PC: 29, HEAD: 4, TOS: 233, 377, 144}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 253, PC: 30, HEAD: 3, TOS: 188, 233, 377}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 254, PC: 31, HEAD: 3, TOS: 188, 233, 377}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 255, PC: 4, HEAD: 3, TOS: 188, 233, 377}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 256, PC: 5, HEAD: 4, TOS: 233, 377, 377}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 257, PC: 6, HEAD: 5, TOS: 377, 377, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 259, PC: 7, HEAD: 4, TOS: 233, 377, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 260, PC: 8, HEAD: 3, TOS: 188, 233, 377}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 261, PC: 9, HEAD: 4, TOS: 233, 377, 377}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 262, PC: 10, HEAD: 5, TOS: 377, 377, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 264, PC: 11, HEAD: 4, TOS: 233, 377, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 266, PC: 12, HEAD: 4, TOS: 233, 377, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 267, PC: 24, HEAD: 3, TOS: 188, 233, 377}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 268, PC: 25, HEAD: 3, TOS: 188, 377, 233}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 269, PC: 26, HEAD: 4, TOS: 377, 233, 377}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 270, PC: 27, HEAD: 5, TOS: 233, 377, 233}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 272, PC: 28, HEAD: 4, TOS: 377, 233, 610}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 273, PC: 29, HEAD: 4, TOS: 377, 610, 233}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 274, PC: 30, HEAD: 3, TOS: 188, 377, 610}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 275, PC: 31, HEAD: 3, TOS: 188, 377, 610}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 276, PC: 4, HEAD: 3, TOS: 188, 377, 610}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 277, PC: 5, HEAD: 4, TOS: 377, 610, 610}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 278, PC: 6, HEAD: 5, TOS: 610, 610, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 280, PC: 7, HEAD: 4, TOS: 377, 610, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 281, PC: 8, HEAD: 3, TOS: 188, 377, 610}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 282, PC: 9, HEAD: 4, TOS: 377, 610, 610}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 283, PC: 10, HEAD: 5, TOS: 610, 610, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 285, PC: 11, HEAD: 4, TOS: 377, 610, 0}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 287, PC: 12, HEAD: 4, TOS: 377, 610, -1}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 288, PC: 13, HEAD: 3, TOS: 188, 377, 610}  ROT  ('None' @ 14:ROT)
DEBUG:root:{TICK: 289, PC: 14, HEAD: 3, TOS: 377, 610, 188}  OVER  ('None' @ 15:OVER)
DEBUG:root:{TICK: 290, PC: 15, HEAD: 4, TOS: 610, 188, 610}  PLUS  ('None' @ 16:PLUS)
DEBUG:root:{TICK: 292, PC: 16, HEAD: 3, TOS: 377, 610, 798}  SWAP  ('None' @ 17:SWAP)
DEBUG:root:{TICK: 293, PC: 17, HEAD: 3, TOS: 377, 798, 610}  ROT  ('None' @ 18:ROT)
DEBUG:root:{TICK: 294, PC: 18, HEAD: 3, TOS: 798, 610, 377}  OVER  ('None' @ 19:OVER)
DEBUG:root:{TICK: 295, PC: 19, HEAD: 4, TOS: 610, 377, 610}  OVER  ('None' @ 20:OVER)
DEBUG:root:{TICK: 296, PC: 20, HEAD: 5, TOS: 377, 610, 377}  PLUS  ('None' @ 21:PLUS)
DEBUG:root:{TICK: 298, PC: 21, HEAD: 4, TOS: 610, 377, 987}  SWAP  ('None' @ 22:SWAP)
DEBUG:root:{TICK: 299, PC: 22, HEAD: 4, TOS: 610, 987, 377}  DROP  ('None' @ 23:DROP)
DEBUG:root:{TICK: 300, PC: 23, HEAD: 3, TOS: 798, 610, 987}  JMP 31 ('None' @ 24:ELSE)
DEBUG:root:{TICK: 301, PC: 31, HEAD: 3, TOS: 798, 610, 987}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 302, PC: 4, HEAD: 3, TOS: 798, 610, 987}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 303, PC: 5, HEAD: 4, TOS: 610, 987, 987}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 304, PC: 6, HEAD: 5, TOS: 987, 987, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 306, PC: 7, HEAD: 4, TOS: 610, 987, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 307, PC: 8, HEAD: 3, TOS: 798, 610, 987}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 308, PC: 9, HEAD: 4, TOS: 610, 987, 987}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 309, PC: 10, HEAD: 5, TOS: 987, 987, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 311, PC: 11, HEAD: 4, TOS: 610, 987, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 313, PC: 12, HEAD: 4, TOS: 610, 987, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 314, PC: 24, HEAD: 3, TOS: 798, 610, 987}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 315, PC: 25, HEAD: 3, TOS: 798, 987, 610}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 316, PC: 26, HEAD: 4, TOS: 987, 610, 987}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 317, PC: 27, HEAD: 5, TOS: 610, 987, 610}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 319, PC: 28, HEAD: 4, TOS: 987, 610, 1597}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 320, PC: 29, HEAD: 4, TOS: 987, 1597, 610}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 321, PC: 30, HEAD: 3, TOS: 798, 987, 1597}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 322, PC: 31, HEAD: 3, TOS: 798, 987, 1597}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 323, PC: 4, HEAD: 3, TOS: 798, 987, 1597}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 324, PC: 5, HEAD: 4, TOS: 987, 1597, 1597}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 325, PC: 6, HEAD: 5, TOS: 1597, 1597, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 327, PC: 7, HEAD: 4, TOS: 987, 1597, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 328, PC: 8, HEAD: 3, TOS: 798, 987, 1597}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 329, PC: 9, HEAD: 4, TOS: 987, 1597, 1597}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 330, PC: 10, HEAD: 5, TOS: 1597, 1597, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 332, PC: 11, HEAD: 4, TOS: 987, 1597, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 334, PC: 12, HEAD: 4, TOS: 987, 1597, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 335, PC: 24, HEAD: 3, TOS: 798, 987, 1597}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 336, PC: 25, HEAD: 3, TOS: 798, 1597, 987}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 337, PC: 26, HEAD: 4, TOS: 1597, 987, 1597}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 338, PC: 27, HEAD: 5, TOS: 987, 1597, 987}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 340, PC: 28, HEAD: 4, TOS: 1597, 987, 2584}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 341, PC: 29, HEAD: 4, TOS: 1597, 2584, 987}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 342, PC: 30, HEAD: 3, TOS: 798, 1597, 2584}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 343, PC: 31, HEAD: 3, TOS: 798, 1597, 2584}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 344, PC: 4, HEAD: 3, TOS: 798, 1597, 2584}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 345, PC: 5, HEAD: 4, TOS: 1597, 2584, 2584}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 346, PC: 6, HEAD: 5, TOS: 2584, 2584, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 348, PC: 7, HEAD: 4, TOS: 1597, 2584, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 349, PC: 8, HEAD: 3, TOS: 798, 1597, 2584}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 350, PC: 9, HEAD: 4, TOS: 1597, 2584, 2584}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 351, PC: 10, HEAD: 5, TOS: 2584, 2584, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 353, PC: 11, HEAD: 4, TOS: 1597, 2584, 0}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 355, PC: 12, HEAD: 4, TOS: 1597, 2584, -1}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 356, PC: 13, HEAD: 3, TOS: 798, 1597, 2584}  ROT  ('None' @ 14:ROT)
DEBUG:root:{TICK: 357, PC: 14, HEAD: 3, TOS: 1597, 2584, 798}  OVER  ('None' @ 15:OVER)
DEBUG:root:{TICK: 358, PC: 15, HEAD: 4, TOS: 2584, 798, 2584}  PLUS  ('None' @ 16:PLUS)
DEBUG:root:{TICK: 360, PC: 16, HEAD: 3, TOS: 1597, 2584, 3382}  SWAP  ('None' @ 17:SWAP)
DEBUG:root:{TICK: 361, PC: 17, HEAD: 3, TOS: 1597, 3382, 2584}  ROT  ('None' @ 18:ROT)
DEBUG:root:{TICK: 362, PC: 18, HEAD: 3, TOS: 3382, 2584, 1597}  OVER  ('None' @ 19:OVER)
DEBUG:root:{TICK: 363, PC: 19, HEAD: 4, TOS: 2584, 1597, 2584}  OVER  ('None' @ 20:OVER)
DEBUG:root:{TICK: 364, PC: 20, HEAD: 5, TOS: 1597, 2584, 1597}  PLUS  ('None' @ 21:PLUS)
DEBUG:root:{TICK: 366, PC: 21, HEAD: 4, TOS: 2584, 1597, 4181}  SWAP  ('None' @ 22:SWAP)
DEBUG:root:{TICK: 367, PC: 22, HEAD: 4, TOS: 2584, 4181, 1597}  DROP  ('None' @ 23:DROP)
DEBUG:root:{TICK: 368, PC: 23, HEAD: 3, TOS: 3382, 2584, 4181}  JMP 31 ('None' @ 24:ELSE)
DEBUG:root:{TICK: 369, PC: 31, HEAD: 3, TOS: 3382, 2584, 4181}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 370, PC: 4, HEAD: 3, TOS: 3382, 2584, 4181}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 371, PC: 5, HEAD: 4, TOS: 2584, 4181, 4181}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 372, PC: 6, HEAD: 5, TOS: 4181, 4181, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 374, PC: 7, HEAD: 4, TOS: 2584, 4181, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 375, PC: 8, HEAD: 3, TOS: 3382, 2584, 4181}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 376, PC: 9, HEAD: 4, TOS: 2584, 4181, 4181}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 377, PC: 10, HEAD: 5, TOS: 4181, 4181, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 379, PC: 11, HEAD: 4, TOS: 2584, 4181, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 381, PC: 12, HEAD: 4, TOS: 2584, 4181, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 382, PC: 24, HEAD: 3, TOS: 3382, 2584, 4181}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 383, PC: 25, HEAD: 3, TOS: 3382, 4181, 2584}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 384, PC: 26, HEAD: 4, TOS: 4181, 2584, 4181}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 385, PC: 27, HEAD: 5, TOS: 2584, 4181, 2584}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 387, PC: 28, HEAD: 4, TOS: 4181, 2584, 6765}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 388, PC: 29, HEAD: 4, TOS: 4181, 6765, 2584}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 389, PC: 30, HEAD: 3, TOS: 3382, 4181, 6765}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 390, PC: 31, HEAD: 3, TOS: 3382, 4181, 6765}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 391, PC: 4, HEAD: 3, TOS: 3382, 4181, 6765}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 392, PC: 5, HEAD: 4, TOS: 4181, 6765, 6765}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 393, PC: 6, HEAD: 5, TOS: 6765, 6765, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 395, PC: 7, HEAD: 4, TOS: 4181, 6765, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 396, PC: 8, HEAD: 3, TOS: 3382, 4181, 6765}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 397, PC: 9, HEAD: 4, TOS: 4181, 6765, 6765}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 398, PC: 10, HEAD: 5, TOS: 6765, 6765, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 400, PC: 11, HEAD: 4, TOS: 4181, 6765, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 402, PC: 12, HEAD: 4, TOS: 4181, 6765, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 403, PC: 24, HEAD: 3, TOS: 3382, 4181, 6765}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 404, PC: 25, HEAD: 3, TOS: 3382, 6765, 4181}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 405, PC: 26, HEAD: 4, TOS: 6765, 4181, 6765}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 406, PC: 27, HEAD: 5, TOS: 4181, 6765, 4181}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 408, PC: 28, HEAD: 4, TOS: 6765, 4181, 10946}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 409, PC: 29, HEAD: 4, TOS: 6765, 10946, 4181}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 410, PC: 30, HEAD: 3, TOS: 3382, 6765, 10946}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 411, PC: 31, HEAD: 3, TOS: 3382, 6765, 10946}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 412, PC: 4, HEAD: 3, TOS: 3382, 6765, 10946}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 413, PC: 5, HEAD: 4, TOS: 6765, 10946, 10946}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 414, PC: 6, HEAD: 5, TOS: 10946, 10946, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 416, PC: 7, HEAD: 4, TOS: 6765, 10946, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 417, PC: 8, HEAD: 3, TOS: 3382, 6765, 10946}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 418, PC: 9, HEAD: 4, TOS: 6765, 10946, 10946}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 419, PC: 10, HEAD: 5, TOS: 10946, 10946, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 421, PC: 11, HEAD: 4, TOS: 6765, 10946, 0}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 423, PC: 12, HEAD: 4, TOS: 6765, 10946, -1}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 424, PC: 13, HEAD: 3, TOS: 3382, 6765, 10946}  ROT  ('None' @ 14:ROT)
DEBUG:root:{TICK: 425, PC: 14, HEAD: 3, TOS: 6765, 10946, 3382}  OVER  ('None' @ 15:OVER)
DEBUG:root:{TICK: 426, PC: 15, HEAD: 4, TOS: 10946, 3382, 10946}  PLUS  ('None' @ 16:PLUS)
DEBUG:root:{TICK: 428, PC: 16, HEAD: 3, TOS: 6765, 10946, 14328}  SWAP  ('None' @ 17:SWAP)
DEBUG:root:{TICK: 429, PC: 17, HEAD: 3, TOS: 6765, 14328, 10946}  ROT  ('None' @ 18:ROT)
DEBUG:root:{TICK: 430, PC: 18, HEAD: 3, TOS: 14328, 10946, 6765}  OVER  ('None' @ 19:OVER)
DEBUG:root:{TICK: 431, PC: 19, HEAD: 4, TOS: 10946, 6765, 10946}  OVER  ('None' @ 20:OVER)
DEBUG:root:{TICK: 432, PC: 20, HEAD: 5, TOS: 6765, 10946, 6765}  PLUS  ('None' @ 21:PLUS)
DEBUG:root:{TICK: 434, PC: 21, HEAD: 4, TOS: 10946, 6765, 17711}  SWAP  ('None' @ 22:SWAP)
DEBUG:root:{TICK: 435, PC: 22, HEAD: 4, TOS: 10946, 17711, 6765}  DROP  ('None' @ 23:DROP)
DEBUG:root:{TICK: 436, PC: 23, HEAD: 3, TOS: 14328, 10946, 17711}  JMP 31 ('None' @ 24:ELSE)
DEBUG:root:{TICK: 437, PC: 31, HEAD: 3, TOS: 14328, 10946, 17711}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 438, PC: 4, HEAD: 3, TOS: 14328, 10946, 17711}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 439, PC: 5, HEAD: 4, TOS: 10946, 17711, 17711}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 440, PC: 6, HEAD: 5, TOS: 17711, 17711, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 442, PC: 7, HEAD: 4, TOS: 10946, 17711, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 443, PC: 8, HEAD: 3, TOS: 14328, 10946, 17711}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 444, PC: 9, HEAD: 4, TOS: 10946, 17711, 17711}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 445, PC: 10, HEAD: 5, TOS: 17711, 17711, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 447, PC: 11, HEAD: 4, TOS: 10946, 17711, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 449, PC: 12, HEAD: 4, TOS: 10946, 17711, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 450, PC: 24, HEAD: 3, TOS: 14328, 10946, 17711}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 451, PC: 25, HEAD: 3, TOS: 14328, 17711, 10946}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 452, PC: 26, HEAD: 4, TOS: 17711, 10946, 17711}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 453, PC: 27, HEAD: 5, TOS: 10946, 17711, 10946}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 455, PC: 28, HEAD: 4, TOS: 17711, 10946, 28657}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 456, PC: 29, HEAD: 4, TOS: 17711, 28657, 10946}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 457, PC: 30, HEAD: 3, TOS: 14328, 17711, 28657}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 458, PC: 31, HEAD: 3, TOS: 14328, 17711, 28657}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 459, PC: 4, HEAD: 3, TOS: 14328, 17711, 28657}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 460, PC: 5, HEAD: 4, TOS: 17711, 28657, 28657}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 461, PC: 6, HEAD: 5, TOS: 28657, 28657, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 463, PC: 7, HEAD: 4, TOS: 17711, 28657, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 464, PC: 8, HEAD: 3, TOS: 14328, 17711, 28657}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 465, PC: 9, HEAD: 4, TOS: 17711, 28657, 28657}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 466, PC: 10, HEAD: 5, TOS: 28657, 28657, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 468, PC: 11, HEAD: 4, TOS: 17711, 28657, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 470, PC: 12, HEAD: 4, TOS: 17711, 28657, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 471, PC: 24, HEAD: 3, TOS: 14328, 17711, 28657}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 472, PC: 25, HEAD: 3, TOS: 14328, 28657, 17711}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 473, PC: 26, HEAD: 4, TOS: 28657, 17711, 28657}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 474, PC: 27, HEAD: 5, TOS: 17711, 28657, 17711}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 476, PC: 28, HEAD: 4, TOS: 28657, 17711, 46368}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 477, PC: 29, HEAD: 4, TOS: 28657, 46368, 17711}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 478, PC: 30, HEAD: 3, TOS: 14328, 28657, 46368}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 479, PC: 31, HEAD: 3, TOS: 14328, 28657, 46368}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 480, PC: 4, HEAD: 3, TOS: 14328, 28657, 46368}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 481, PC: 5, HEAD: 4, TOS: 28657, 46368, 46368}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 482, PC: 6, HEAD: 5, TOS: 46368, 46368, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 484, PC: 7, HEAD: 4, TOS: 28657, 46368, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 485, PC: 8, HEAD: 3, TOS: 14328, 28657, 46368}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 486, PC: 9, HEAD: 4, TOS: 28657, 46368, 46368}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 487, PC: 10, HEAD: 5, TOS: 46368, 46368, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 489, PC: 11, HEAD: 4, TOS: 28657, 46368, 0}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 491, PC: 12, HEAD: 4, TOS: 28657, 46368, -1}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 492, PC: 13, HEAD: 3, TOS: 14328, 28657, 46368}  ROT  ('None' @ 14:ROT)
DEBUG:root:{TICK: 493, PC: 14, HEAD: 3, TOS: 28657, 46368, 14328}  OVER  ('None' @ 15:OVER)
DEBUG:root:{TICK: 494, PC: 15, HEAD: 4, TOS: 46368, 14328, 46368}  PLUS  ('None' @ 16:PLUS)
DEBUG:root:{TICK: 496, PC: 16, HEAD: 3, TOS: 28657, 46368, 60696}  SWAP  ('None' @ 17:SWAP)
DEBUG:root:{TICK: 497, PC: 17, HEAD: 3, TOS: 28657, 60696, 46368}  ROT  ('None' @ 18:ROT)
DEBUG:root:{TICK: 498, PC: 18, HEAD: 3, TOS: 60696, 46368, 28657}  OVER  ('None' @ 19:OVER)
DEBUG:root:{TICK: 499, PC: 19, HEAD: 4, TOS: 46368, 28657, 46368}  OVER  ('None' @ 20:OVER)
DEBUG:root:{TICK: 500, PC: 20, HEAD: 5, TOS: 28657, 46368, 28657}  PLUS  ('None' @ 21:PLUS)
DEBUG:root:{TICK: 502, PC: 21, HEAD: 4, TOS: 46368, 28657, 75025}  SWAP  ('None' @ 22:SWAP)
DEBUG:root:{TICK: 503, PC: 22, HEAD: 4, TOS: 46368, 75025, 28657}  DROP  ('None' @ 23:DROP)
DEBUG:root:{TICK: 504, PC: 23, HEAD: 3, TOS: 60696, 46368, 75025}  JMP 31 ('None' @ 24:ELSE)
DEBUG:root:{TICK: 505, PC: 31, HEAD: 3, TOS: 60696, 46368, 75025}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 506, PC: 4, HEAD: 3, TOS: 60696, 46368, 75025}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 507, PC: 5, HEAD: 4, TOS: 46368, 75025, 75025}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 508, PC: 6, HEAD: 5, TOS: 75025, 75025, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 510, PC: 7, HEAD: 4, TOS: 46368, 75025, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 511, PC: 8, HEAD: 3, TOS: 60696, 46368, 75025}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 512, PC: 9, HEAD: 4, TOS: 46368, 75025, 75025}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 513, PC: 10, HEAD: 5, TOS: 75025, 75025, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 515, PC: 11, HEAD: 4, TOS: 46368, 75025, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 517, PC: 12, HEAD: 4, TOS: 46368, 75025, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 518, PC: 24, HEAD: 3, TOS: 60696, 46368, 75025}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 519, PC: 25, HEAD: 3, TOS: 60696, 75025, 46368}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 520, PC: 26, HEAD: 4, TOS: 75025, 46368, 75025}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 521, PC: 27, HEAD: 5, TOS: 46368, 75025, 46368}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 523, PC: 28, HEAD: 4, TOS: 75025, 46368, 121393}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 524, PC: 29, HEAD: 4, TOS: 75025, 121393, 46368}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 525, PC: 30, HEAD: 3, TOS: 60696, 75025, 121393}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 526, PC: 31, HEAD: 3, TOS: 60696, 75025, 121393}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 527, PC: 4, HEAD: 3, TOS: 60696, 75025, 121393}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 528, PC: 5, HEAD: 4, TOS: 75025, 121393, 121393}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 529, PC: 6, HEAD: 5, TOS: 121393, 121393, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 531, PC: 7, HEAD: 4, TOS: 75025, 121393, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 532, PC: 8, HEAD: 3, TOS: 60696, 75025, 121393}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 533, PC: 9, HEAD: 4, TOS: 75025, 121393, 121393}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 534, PC: 10, HEAD: 5, TOS: 121393, 121393, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 536, PC: 11, HEAD: 4, TOS: 75025, 121393, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 538, PC: 12, HEAD: 4, TOS: 75025, 121393, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 539, PC: 24, HEAD: 3, TOS: 60696, 75025, 121393}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 540, PC: 25, HEAD: 3, TOS: 60696, 121393, 75025}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 541, PC: 26, HEAD: 4, TOS: 121393, 75025, 121393}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 542, PC: 27, HEAD: 5, TOS: 75025, 121393, 75025}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 544, PC: 28, HEAD: 4, TOS: 121393, 75025, 196418}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 545, PC: 29, HEAD: 4, TOS: 121393, 196418, 75025}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 546, PC: 30, HEAD: 3, TOS: 60696, 121393, 196418}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 547, PC: 31, HEAD: 3, TOS: 60696, 121393, 196418}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 548, PC: 4, HEAD: 3, TOS: 60696, 121393, 196418}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 549, PC: 5, HEAD: 4, TOS: 121393, 196418, 196418}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 550, PC: 6, HEAD: 5, TOS: 196418, 196418, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 552, PC: 7, HEAD: 4, TOS: 121393, 196418, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 553, PC: 8, HEAD: 3, TOS: 60696, 121393, 196418}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 554, PC: 9, HEAD: 4, TOS: 121393, 196418, 196418}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 555, PC: 10, HEAD: 5, TOS: 196418, 196418, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 557, PC: 11, HEAD: 4, TOS: 121393, 196418, 0}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 559, PC: 12, HEAD: 4, TOS: 121393, 196418, -1}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 560, PC: 13, HEAD: 3, TOS: 60696, 121393, 196418}  ROT  ('None' @ 14:ROT)
DEBUG:root:{TICK: 561, PC: 14, HEAD: 3, TOS: 121393, 196418, 60696}  OVER  ('None' @ 15:OVER)
DEBUG:root:{TICK: 562, PC: 15, HEAD: 4, TOS: 196418, 60696, 196418}  PLUS  ('None' @ 16:PLUS)
DEBUG:root:{TICK: 564, PC: 16, HEAD: 3, TOS: 121393, 196418, 257114}  SWAP  ('None' @ 17:SWAP)
DEBUG:root:{TICK: 565, PC: 17, HEAD: 3, TOS: 121393, 257114, 196418}  ROT  ('None' @ 18:ROT)
DEBUG:root:{TICK: 566, PC: 18, HEAD: 3, TOS: 257114, 196418, 121393}  OVER  ('None' @ 19:OVER)
DEBUG:root:{TICK: 567, PC: 19, HEAD: 4, TOS: 196418, 121393, 196418}  OVER  ('None' @ 20:OVER)
DEBUG:root:{TICK: 568, PC: 20, HEAD: 5, TOS: 121393, 196418, 121393}  PLUS  ('None' @ 21:PLUS)
DEBUG:root:{TICK: 570, PC: 21, HEAD: 4, TOS: 196418, 121393, 317811}  SWAP  ('None' @ 22:SWAP)
DEBUG:root:{TICK: 571, PC: 22, HEAD: 4, TOS: 196418, 317811, 121393}  DROP  ('None' @ 23:DROP)
DEBUG:root:{TICK: 572, PC: 23, HEAD: 3, TOS: 257114, 196418, 317811}  JMP 31 ('None' @ 24:ELSE)
DEBUG:root:{TICK: 573, PC: 31, HEAD: 3, TOS: 257114, 196418, 317811}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 574, PC: 4, HEAD: 3, TOS: 257114, 196418, 317811}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 575, PC: 5, HEAD: 4, TOS: 196418, 317811, 317811}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 576, PC: 6, HEAD: 5, TOS: 317811, 317811, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 578, PC: 7, HEAD: 4, TOS: 196418, 317811, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 579, PC: 8, HEAD: 3, TOS: 257114, 196418, 317811}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 580, PC: 9, HEAD: 4, TOS: 196418, 317811, 317811}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 581, PC: 10, HEAD: 5, TOS: 317811, 317811, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 583, PC: 11, HEAD: 4, TOS: 196418, 317811, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 585, PC: 12, HEAD: 4, TOS: 196418, 317811, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 586, PC: 24, HEAD: 3, TOS: 257114, 196418, 317811}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 587, PC: 25, HEAD: 3, TOS: 257114, 317811, 196418}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 588, PC: 26, HEAD: 4, TOS: 317811, 196418, 317811}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 589, PC: 27, HEAD: 5, TOS: 196418, 317811, 196418}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 591, PC: 28, HEAD: 4, TOS: 317811, 196418, 514229}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 592, PC: 29, HEAD: 4, TOS: 317811, 514229, 196418}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 593, PC: 30, HEAD: 3, TOS: 257114, 317811, 514229}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 594, PC: 31, HEAD: 3, TOS: 257114, 317811, 514229}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 595, PC: 4, HEAD: 3, TOS: 257114, 317811, 514229}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 596, PC: 5, HEAD: 4, TOS: 317811, 514229, 514229}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 597, PC: 6, HEAD: 5, TOS: 514229, 514229, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 599, PC: 7, HEAD: 4, TOS: 317811, 514229, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 600, PC: 8, HEAD: 3, TOS: 257114, 317811, 514229}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 601, PC: 9, HEAD: 4, TOS: 317811, 514229, 514229}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 602, PC: 10, HEAD: 5, TOS: 514229, 514229, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 604, PC: 11, HEAD: 4, TOS: 317811, 514229, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 606, PC: 12, HEAD: 4, TOS: 317811, 514229, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 607, PC: 24, HEAD: 3, TOS: 257114, 317811, 514229}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 608, PC: 25, HEAD: 3, TOS: 257114, 514229, 317811}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 609, PC: 26, HEAD: 4, TOS: 514229, 317811, 514229}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 610, PC: 27, HEAD: 5, TOS: 317811, 514229, 317811}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 612, PC: 28, HEAD: 4, TOS: 514229, 317811, 832040}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 613, PC: 29, HEAD: 4, TOS: 514229, 832040, 317811}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 614, PC: 30, HEAD: 3, TOS: 257114, 514229, 832040}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 615, PC: 31, HEAD: 3, TOS: 257114, 514229, 832040}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 616, PC: 4, HEAD: 3, TOS: 257114, 514229, 832040}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 617, PC: 5, HEAD: 4, TOS: 514229, 832040, 832040}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 618, PC: 6, HEAD: 5, TOS: 832040, 832040, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 620, PC: 7, HEAD: 4, TOS: 514229, 832040, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 621, PC: 8, HEAD: 3, TOS: 257114, 514229, 832040}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 622, PC: 9, HEAD: 4, TOS: 514229, 832040, 832040}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 623, PC: 10, HEAD: 5, TOS: 832040, 832040, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 625, PC: 11, HEAD: 4, TOS: 514229, 832040, 0}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 627, PC: 12, HEAD: 4, TOS: 514229, 832040, -1}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 628, PC: 13, HEAD: 3, TOS: 257114, 514229, 832040}  ROT  ('None' @ 14:ROT)
DEBUG:root:{TICK: 629, PC: 14, HEAD: 3, TOS: 514229, 832040, 257114}  OVER  ('None' @ 15:OVER)
DEBUG:root:{TICK: 630, PC: 15, HEAD: 4, TOS: 832040, 257114, 832040}  PLUS  ('None' @ 16:PLUS)
DEBUG:root:{TICK: 632, PC: 16, HEAD: 3, TOS: 514229, 832040, 1089154}  SWAP  ('None' @ 17:SWAP)
DEBUG:root:{TICK: 633, PC: 17, HEAD: 3, TOS: 514229, 1089154, 832040}  ROT  ('None' @ 18:ROT)
DEBUG:root:{TICK: 634, PC: 18, HEAD: 3, TOS: 1089154, 832040, 514229}  OVER  ('None' @ 19:OVER)
DEBUG:root:{TICK: 635, PC: 19, HEAD: 4, TOS: 832040, 514229, 832040}  OVER  ('None' @ 20:OVER)
DEBUG:root:{TICK: 636, PC: 20, HEAD: 5, TOS: 514229, 832040, 514229}  PLUS  ('None' @ 21:PLUS)
DEBUG:root:{TICK: 638, PC: 21, HEAD: 4, TOS: 832040, 514229, 1346269}  SWAP  ('None' @ 22:SWAP)
DEBUG:root:{TICK: 639, PC: 22, HEAD: 4, TOS: 832040, 1346269, 514229}  DROP  ('None' @ 23:DROP)
DEBUG:root:{TICK: 640, PC: 23, HEAD: 3, TOS: 1089154, 832040, 1346269}  JMP 31 ('None' @ 24:ELSE)
DEBUG:root:{TICK: 641, PC: 31, HEAD: 3, TOS: 1089154, 832040, 1346269}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 642, PC: 4, HEAD: 3, TOS: 1089154, 832040, 1346269}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 643, PC: 5, HEAD: 4, TOS: 832040, 1346269, 1346269}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 644, PC: 6, HEAD: 5, TOS: 1346269, 1346269, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 646, PC: 7, HEAD: 4, TOS: 832040, 1346269, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 647, PC: 8, HEAD: 3, TOS: 1089154, 832040, 1346269}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 648, PC: 9, HEAD: 4, TOS: 832040, 1346269, 1346269}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 649, PC: 10, HEAD: 5, TOS: 1346269, 1346269, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 651, PC: 11, HEAD: 4, TOS: 832040, 1346269, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 653, PC: 12, HEAD: 4, TOS: 832040, 1346269, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 654, PC: 24, HEAD: 3, TOS: 1089154, 832040, 1346269}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 655, PC: 25, HEAD: 3, TOS: 1089154, 1346269, 832040}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 656, PC: 26, HEAD: 4, TOS: 1346269, 832040, 1346269}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 657, PC: 27, HEAD: 5, TOS: 832040, 1346269, 832040}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 659, PC: 28, HEAD: 4, TOS: 1346269, 832040, 2178309}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 660, PC: 29, HEAD: 4, TOS: 1346269, 2178309, 832040}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 661, PC: 30, HEAD: 3, TOS: 1089154, 1346269, 2178309}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 662, PC: 31, HEAD: 3, TOS: 1089154, 1346269, 2178309}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 663, PC: 4, HEAD: 3, TOS: 1089154, 1346269, 2178309}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 664, PC: 5, HEAD: 4, TOS: 1346269, 2178309, 2178309}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 665, PC: 6, HEAD: 5, TOS: 2178309, 2178309, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 667, PC: 7, HEAD: 4, TOS: 1346269, 2178309, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 668, PC: 8, HEAD: 3, TOS: 1089154, 1346269, 2178309}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 669, PC: 9, HEAD: 4, TOS: 1346269, 2178309, 2178309}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 670, PC: 10, HEAD: 5, TOS: 2178309, 2178309, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 672, PC: 11, HEAD: 4, TOS: 1346269, 2178309, 1}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 674, PC: 12, HEAD: 4, TOS: 1346269, 2178309, -2}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 675, PC: 24, HEAD: 3, TOS: 1089154, 1346269, 2178309}  SWAP  ('None' @ 25:SWAP)
DEBUG:root:{TICK: 676, PC: 25, HEAD: 3, TOS: 1089154, 2178309, 1346269}  OVER  ('None' @ 26:OVER)
DEBUG:root:{TICK: 677, PC: 26, HEAD: 4, TOS: 2178309, 1346269, 2178309}  OVER  ('None' @ 27:OVER)
DEBUG:root:{TICK: 678, PC: 27, HEAD: 5, TOS: 1346269, 2178309, 1346269}  PLUS  ('None' @ 28:PLUS)
DEBUG:root:{TICK: 680, PC: 28, HEAD: 4, TOS: 2178309, 1346269, 3524578}  SWAP  ('None' @ 29:SWAP)
DEBUG:root:{TICK: 681, PC: 29, HEAD: 4, TOS: 2178309, 3524578, 1346269}  DROP  ('None' @ 30:DROP)
DEBUG:root:{TICK: 682, PC: 30, HEAD: 3, TOS: 1089154, 2178309, 3524578}  NOP  ('None' @ 31:ENDIF)
DEBUG:root:{TICK: 683, PC: 31, HEAD: 3, TOS: 1089154, 2178309, 3524578}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 684, PC: 4, HEAD: 3, TOS: 1089154, 2178309, 3524578}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 685, PC: 5, HEAD: 4, TOS: 2178309, 3524578, 3524578}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 686, PC: 6, HEAD: 5, TOS: 3524578, 3524578, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 688, PC: 7, HEAD: 4, TOS: 2178309, 3524578, -1}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 689, PC: 8, HEAD: 3, TOS: 1089154, 2178309, 3524578}  DUP  ('None' @ 9:DUP)
DEBUG:root:{TICK: 690, PC: 9, HEAD: 4, TOS: 2178309, 3524578, 3524578}  PUSH 2 ('2' @ 10:PUSH)
DEBUG:root:{TICK: 691, PC: 10, HEAD: 5, TOS: 3524578, 3524578, 2}  MOD  ('None' @ 11:MOD)
DEBUG:root:{TICK: 693, PC: 11, HEAD: 4, TOS: 2178309, 3524578, 0}  INVERT  ('None' @ 12:INVERT)
DEBUG:root:{TICK: 695, PC: 12, HEAD: 4, TOS: 2178309, 3524578, -1}  JNT 24 ('None' @ 13:IF)
DEBUG:root:{TICK: 696, PC: 13, HEAD: 3, TOS: 1089154, 2178309, 3524578}  ROT  ('None' @ 14:ROT)
DEBUG:root:{TICK: 697, PC: 14, HEAD: 3, TOS: 2178309, 3524578, 1089154}  OVER  ('None' @ 15:OVER)
DEBUG:root:{TICK: 698, PC: 15, HEAD: 4, TOS: 3524578, 1089154, 3524578}  PLUS  ('None' @ 16:PLUS)
DEBUG:root:{TICK: 700, PC: 16, HEAD: 3, TOS: 2178309, 3524578, 4613732}  SWAP  ('None' @ 17:SWAP)
DEBUG:root:{TICK: 701, PC: 17, HEAD: 3, TOS: 2178309, 4613732, 3524578}  ROT  ('None' @ 18:ROT)
DEBUG:root:{TICK: 702, PC: 18, HEAD: 3, TOS: 4613732, 3524578, 2178309}  OVER  ('None' @ 19:OVER)
DEBUG:root:{TICK: 703, PC: 19, HEAD: 4, TOS: 3524578, 2178309, 3524578}  OVER  ('None' @ 20:OVER)
DEBUG:root:{TICK: 704, PC: 20, HEAD: 5, TOS: 2178309, 3524578, 2178309}  PLUS  ('None' @ 21:PLUS)
DEBUG:root:{TICK: 706, PC: 21, HEAD: 4, TOS: 3524578, 2178309, 5702887}  SWAP  ('None' @ 22:SWAP)
DEBUG:root:{TICK: 707, PC: 22, HEAD: 4, TOS: 3524578, 5702887, 2178309}  DROP  ('None' @ 23:DROP)
DEBUG:root:{TICK: 708, PC: 23, HEAD: 3, TOS: 4613732, 3524578, 5702887}  JMP 31 ('None' @ 24:ELSE)
DEBUG:root:{TICK: 709, PC: 31, HEAD: 3, TOS: 4613732, 3524578, 5702887}  JMP 4 ('None' @ 32:REPEAT)
DEBUG:root:{TICK: 710, PC: 4, HEAD: 3, TOS: 4613732, 3524578, 5702887}  DUP  ('None' @ 5:DUP)
DEBUG:root:{TICK: 711, PC: 5, HEAD: 4, TOS: 3524578, 5702887, 5702887}  PUSH 4000000 ('4000000' @ 6:PUSH)
DEBUG:root:{TICK: 712, PC: 6, HEAD: 5, TOS: 5702887, 5702887, 4000000}  LT  ('None' @ 7:LT)
DEBUG:root:{TICK: 714, PC: 7, HEAD: 4, TOS: 3524578, 5702887, 0}  JNT 32 ('None' @ 8:WHILE)
DEBUG:root:{TICK: 715, PC: 32, HEAD: 3, TOS: 4613732, 3524578, 5702887}  ROT  ('None' @ 33:ROT)
DEBUG:root:{TICK: 716, PC: 33, HEAD: 3, TOS: 3524578, 5702887, 4613732}  WRITE_OUT  ('None' @ 34:WRITE_OUT)
INFO:root:output:  << 4613732
DEBUG:root:{TICK: 718, PC: 34, HEAD: 2, TOS: 0, 3524578, 5702887}  HALT  ('None' @ 35:HALT)
instr_counter:  581 ticks:  718
output: 4613732
```

| ФИО         | алг.  | code байт | code инстр. | инстр. | такт. | вариант                                                  |
|-------------|-------|-----------|-------------|--------|-------|----------------------------------------------------------|
| Панчук М.К. | hello | -         | 12          | 105    | 169   | forth, stack, neum, hw, instr, struct, trap, port, prob2 |
| Панчук М.К. | cat   | -         | 9           | limit  | 310   | forth, stack, neum, hw, instr, struct, trap, port, prob2 |
| Панчук М.К. | prob2 | -         | 40          | 581    | 718   | forth, stack, neum, hw, instr, struct, trap, port, prob2 |