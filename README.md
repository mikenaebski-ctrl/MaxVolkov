# UNIX shell emulator (вариант 6)

Практическая работа по курсу «Конфигурационное управление», РТУ МИРЭА.
Репозиторий: https://github.com/mikenaebski-ctrl/MaxVolkov

## Общее описание

Эмулятор оболочки UNIX-подобной ОС с графическим интерфейсом (tkinter).
Пользователь вводит команды в окне, эмулятор разбирает строку по правилам
кавычек UNIX, выполняет команду и выводит результат в историю окна.
Команды не передаются оболочке реальной ОС: файловая система виртуальная
(VFS), она загружается из ZIP-архива в память и существует только там.

Выполнены все пять этапов задания:

1. REPL: GUI, парсер с кавычками, обработка ошибок, `exit`.
2. Конфигурация: параметры `--vfs` и `--script`, стартовый скрипт.
3. VFS: загрузка ZIP-архива в память, ошибки загрузки.
4. Основные команды: `ls`, `cd`, `cat`, `tree`, `whoami`.
5. Дополнительные команды: `mv`.

Заголовок окна содержит имя VFS: `UNIX shell - <имя>`, где имя это имя
файла архива из `--vfs` (без параметра `demo-vfs`). Приглашение:
`пользователь@имя:/текущая/папка$`. Пользователь это имя пользователя ОС
(`getpass.getuser()`), а если определить его не удалось, то `student`.
В примерах ниже пользователь `student`.

## Требования и запуск

Python 3.9 или новее, только стандартная библиотека и tkinter. Запуск из
корня проекта.

macOS / Linux: `sh run.sh`. Windows: `run.bat`. Или напрямую:
`python3 -B -m src`. Параметры передаются после команды запуска:

```sh
sh run.sh --vfs disk.zip --script examples/all_commands.txt
```

Для запуска нужен tkinter. Проверка:

```sh
python3 -c "import tkinter"
python3 -m tkinter
```

Вторая команда открывает тестовое окно Tk. Если модуля нет, установите
Python с поддержкой Tcl/Tk (например, с python.org).

## Параметры командной строки

| Параметр | Значение |
| --- | --- |
| `--vfs PATH` | путь к физическому расположению VFS (ZIP-архив) |
| `--script PATH` | путь к стартовому скрипту |

При запуске все параметры выводятся для отладки: в консоль (stdout) и в
начало истории окна, например `debug: vfs = disk.zip`; незаданный
параметр выводится как `(not set)`. Неизвестный параметр или параметр
без значения завершают запуск сообщением argparse (код 2).

## Стартовый скрипт

Скрипт выполняется сразу после открытия окна. Каждая строка показывается
с приглашением, как будто её ввёл пользователь, затем выводится результат.
Формат: одна команда на строку, кавычки как в обычном вводе.

- комментарий начинается с `#` в начале слова вне кавычек (целая строка
  или конец строки); `'a # b'` и `a#b` комментариями не являются;
- пустые строки пропускаются;
- ошибка команды (неизвестная команда, неверные аргументы, незакрытая
  кавычка) выводится как в диалоге, затем `script: line N: command
  failed`; выполнение продолжается, в конце выводится
  `script: finished with K error(s)`;
- нечитаемый или несуществующий скрипт даёт
  `error: script: cannot read 'путь': причина`, окно остаётся для
  ручного ввода;
- `exit` в скрипте закрывает окно и прекращает выполнение.

## VFS

Параметр `--vfs` указывает ZIP-архив, который загружается в память:

- архив читается через `zipfile` и не распаковывается на диск; файл
  архива не изменяется, команды меняют только копию в памяти;
- каталоги создаются и по явным записям архива, и по путям файлов;
- текстовые файлы (UTF-8) хранятся как текст, двоичные (или содержащие
  байт `0x00`) хранятся как строка base64, `cat` выводит её как есть;
- ошибки загрузки не роняют приложение: сообщение `error: vfs: ...`
  выводится в окно и в stderr, оболочка остаётся доступной (файловые
  команды отвечают `no VFS loaded`). Случаи: файл не найден, указан
  каталог, не ZIP / повреждённый / обрезанный архив (в том числе ошибка
  контрольной суммы), путь вне корня (`../x`, `/x`), совпадение имени
  файла и каталога.

Архивы в репозитории не хранятся. Тестовые ZIP создаёт
`tests/make_vfs.py` (в тестах и в скриптах ОС), вручную:

```sh
python3 tests/make_vfs.py /tmp/vfs
```

Создаются: `minimal.zip` (один файл), `empty.zip`, `several.zip` (файлы
и папки, пробел и Unicode в именах), `deep.zip` (4 уровня и пустая
папка), `binary.zip` (двоичный файл), `rich.zip` (скрытые файлы,
двоичный файл, вложенные и пустая папки), а также некорректные
`not_a_zip.zip`, `truncated.zip`, `corrupt.zip`, `unsafe.zip`,
`clash.zip`.

## Команды

Пути поддерживаются абсолютные (`/docs`) и относительные, с `.` и `..`;
выше корня подняться нельзя (`cd ..` в корне остаётся в корне). Команды,
которым нужна VFS, без неё отвечают `error: <команда>: no VFS loaded`.

| Команда | Режимы | Результат |
| --- | --- | --- |
| `ls [-a] [-l] [путь...]` | без пути: текущая папка; `-a` скрытые и `.`, `..`; `-l` тип (`d`/`-`), размер, имя; `-la` вместе; `--` конец опций | содержимое папки по именам; для файла его имя; при нескольких путях у папок заголовки `путь:`; ошибочный путь не мешает остальным |
| `cd [путь]` | без пути: в корень | меняет текущую папку; ошибки `No such file or directory`, `Not a directory`; больше одного пути: `expected at most one path` |
| `cat файл...` | несколько файлов подряд | текст как есть, двоичные данные в base64; `Is a directory`, `No such file or directory`, `missing file operand` |
| `tree [-a] [-L N] [путь]` | `-a` скрытые; `-L N` или `-LN` глубина | дерево с `├──`, `└──`, `│`, затем `N directories, M files` |
| `mv [-n] [-v] источник... приёмник` | `-n` не перезаписывать существующее (молча пропустить); `-v` печатать `renamed 'a' -> 'b'` | переименует или переместит записи только в памяти |
| `whoami` | без аргументов | имя пользователя из приглашения |
| `exit` | без аргументов | закрывает окно |
| `vfs-info [--list]` | служебная | имя, число папок и файлов, размер; с `--list` все пути (`text` или `base64`, размер) |

Правила `mv` (как в GNU mv):

- приёмник существует и это папка: источники попадают внутрь под своими
  именами; иначе это новое имя (источник должен быть один, а папка
  приёмника существовать: `target '...' is not a directory`);
- файл заменяет файл; папка заменяет только пустую папку (`Directory not
  empty`); папку на файл и файл на папку заменить нельзя;
- запрещены перемещение в собственное поддерево (`cannot move 'a' to a
  subdirectory of itself`), на себя (`are the same file`), корня, а также
  `.` и `..` (`Device or resource busy`);
- ошибочный источник не мешает остальным: остальные перемещаются, а
  ошибка выводится;
- если перемещена папка, в которой (или внутри которой) вы стоите,
  текущая папка следует за ней, приглашение обновляется;
- изменения живут только в памяти и пропадают после закрытия окна.

Файлы и папки, имена которых начинаются с точки, считаются скрытыми.
Неизвестная опция даёт `invalid option -- 'x'`. Пустая строка
игнорируется. Имена команд чувствительны к регистру.

## Примеры использования

Вывод получен запуском кода эмулятора на архивах `tests/make_vfs.py`.

**Этап 1.** Парсер и ошибки (без VFS; `"two words"` это один аргумент):

```text
student@demo-vfs:/$ whoami "two words"
error: whoami: extra operand 'two words'
student@demo-vfs:/$ ls
error: ls: no VFS loaded
student@demo-vfs:/$ missing
error: missing: command not found
student@demo-vfs:/$ ls "unfinished
error: parse: No closing quotation
student@demo-vfs:/$ exit now
error: exit: expected no arguments
student@demo-vfs:/$ exit
exit
```

**Этап 2.** Отладочный вывод параметров и стартовый скрипт с ошибками
(`sh run.sh --script examples/stage2_errors.txt`):

```text
debug: vfs = (not set)
debug: script = examples/stage2_errors.txt
student@demo-vfs:/$ whoami extra
error: whoami: extra operand 'extra'
script: line 2: command failed
student@demo-vfs:/$ missing_command
error: missing_command: command not found
script: line 3: command failed
student@demo-vfs:/$ cd one two
error: cd: expected at most one path
script: line 4: command failed
student@demo-vfs:/$ ls "unfinished
error: parse: No closing quotation
script: line 5: command failed
student@demo-vfs:/$ whoami
student
student@demo-vfs:/$ exit
exit
```

**Этап 3.** Загрузка VFS (`--vfs several.zip`) и ошибка загрузки
(`--vfs not_a_zip.zip`, в окно и в stderr):

```text
vfs: loaded several.zip (2 directories, 4 files)
student@several.zip:/$ vfs-info --list
vfs: several.zip
directories: 2
files: 4 (0 binary)
size: 85 B
/My Documents/
/My Documents/hello.txt  text  27 B
/a.txt  text  11 B
/b.txt  text  22 B
/notes/
/notes/todo.txt  text  25 B
student@several.zip:/$ vfs-info --bogus
error: vfs-info: unknown option '--bogus'
```

```text
error: vfs: cannot load '/tmp/vfs/not_a_zip.zip': invalid ZIP archive (File is not a zip file)
```

**Этап 4.** Основные команды на `rich.zip`:

```text
student@rich.zip:/$ ls -la
d      0 .
d      0 ..
-     12 .hidden
d      0 docs
d      0 empty
-     21 readme.txt
d      0 src
student@rich.zip:/$ cd docs/img
student@rich.zip:/docs/img$ cat logo.bin
AAECAwQFBgc=
student@rich.zip:/docs/img$ cd ../..
student@rich.zip:/$ tree -L 2
.
├── docs
│   ├── guide.txt
│   └── img
├── empty
├── readme.txt
└── src
    ├── lib
    └── main.py

5 directories, 3 files
student@rich.zip:/$ cat readme.txt docs
Rich VFS
second line
error: cat: docs: Is a directory
student@rich.zip:/$ cd nothing
error: cd: nothing: No such file or directory
student@rich.zip:/$ ls -z
error: ls: invalid option -- 'z'
student@rich.zip:/$ whoami
student
```

**Этап 5.** `mv` на `rich.zip` (команда `mv -n` ничего не выводит и не
перезаписывает файл):

```text
student@rich.zip:/$ mv -v readme.txt docs
renamed 'readme.txt' -> 'docs/readme.txt'
student@rich.zip:/$ mv src docs/src
student@rich.zip:/$ cd docs
student@rich.zip:/docs$ mv /docs /library
student@rich.zip:/library$ ls
guide.txt
img
readme.txt
src
student@rich.zip:/library$ mv /library /library/inner
error: mv: cannot move '/library' to a subdirectory of itself, '/library/inner'
student@rich.zip:/library$ mv nothing /library
error: mv: cannot stat 'nothing': No such file or directory
student@rich.zip:/library$ mv -n /library/readme.txt /library/guide.txt
student@rich.zip:/library$ exit
exit
```

## Структура проекта

```
src/
  __main__.py      точка входа (python3 -m src)
  gui.py           окно tkinter: история, строка ввода, Enter
  parser.py        разбор строки с кавычками (shlex), срез комментариев
  config.py        параметры командной строки (argparse), отладочный вывод
  script.py        чтение и воспроизведение стартового скрипта
  shell.py         выполнение команд через словарь COMMANDS
  session.py       создание оболочки: загрузка VFS, сообщения
  vfs.py           VFS в памяти и загрузка из ZIP
  resolve.py       разбор путей (., .., абсолютные и относительные)
  user.py          имя пользователя ОС (getpass) с запасным student
  result.py        результат команды: текст, ошибка, признак выхода
  errors.py        ожидаемые ошибки команд
  constants.py     именованные настройки
  commands/
    __init__.py    словарь COMMANDS: имя команды -> функция
    fs.py          ls, cd, cat
    tree.py        tree
    mv.py          mv
    whoami.py      whoami
    vfs_info.py    vfs-info
    repl.py        exit
    options.py     разбор коротких опций (-a, -L N, --)
    common.py      общие помощники файловых команд
tests/             модульные тесты (unittest) и проверки ограничений кода
  make_vfs.py      генератор тестовых ZIP (архивов в git нет)
  scripts/         скрипты ОС (sh) с вызовами эмулятора
examples/          стартовые скрипты эмулятора для демонстрации
run.sh, run.bat    запуск на macOS/Linux и на Windows
```

## Тесты

Сборка не требуется. Запуск тестов из корня проекта:

```sh
python3 -B -m unittest discover -s tests -v
```

Тесты не требуют tkinter и экрана. Они проверяют:

- парсер: кавычки, экранирование, пустые аргументы, комментарии;
- оболочку: ошибки, восстановление после ошибки, `exit`, `no VFS loaded`;
- имя пользователя: `getpass`, запасное значение, явное имя;
- конфигурацию: разбор `--vfs` и `--script`, ошибки параметров;
- скрипт: комментарии, пропуск пустых строк, ошибки, `exit`;
- VFS: минимальный, пустой, несколько файлов, 4 уровня, base64, все
  ошибки загрузки, неизменность архива; команду `vfs-info`;
- `ls`, `cd`, `cat`, `tree`, `whoami`: все режимы, пути, ошибки и
  частичный вывод при нескольких операндах;
- `mv`: переименование, перемещение, несколько источников, перезапись,
  `-n`, `-v`, все ошибки, слежение текущей папки, архив не меняется;
- ограничения кода (`tests/test_quality.py`): длина строк (до 80) и
  функций (до 40), число аргументов (до 7), цикломатическая сложность
  (до 10), docstring, отсутствие чисел в сравнениях, размер файлов.

## Скрипты ОС и стартовые скрипты

Каждый скрипт в `tests/scripts/` запускает эмулятор с параметрами
(откроется окно; скрипты этапов 3-5 создают тестовые ZIP во временном
каталоге и удаляют его при выходе). Стартовые скрипты эмулятора лежат в
`examples/` и заканчиваются `exit`, поэтому окно закрывается само.

| Этап | Скрипты ОС | Стартовые скрипты |
| --- | --- | --- |
| 2 | `stage2_no_params.sh`, `stage2_vfs_param.sh`, `stage2_script_param.sh`, `stage2_both_and_errors.sh` | `stage2_basic.txt`, `stage2_errors.txt` |
| 3 | `stage3_minimal.sh`, `stage3_several.sh`, `stage3_deep.sh`, `stage3_errors.sh` | `stage3_vfs_info.txt` |
| 4 | `stage4_rich.sh`, `stage4_deep.sh`, `stage4_no_vfs.sh` | `stage4_commands.txt`, `stage4_deep.txt` |
| 5 | `stage5_rich.sh`, `stage5_deep.sh`, `stage5_no_vfs.sh` | `stage5_mv.txt`, `stage5_deep.txt` |

Общий скрипт `examples/all_commands.txt` проверяет все команды и режимы
этапов 1-5 вместе с ошибками (`stage4_rich.sh` и `stage5_rich.sh`
запускают его на `rich.zip`). Запуск, например:

```sh
sh tests/scripts/stage5_rich.sh
```
