# UNIX shell emulator: variant 6

Практическая работа по курсу «Конфигурационное управление», РТУ МИРЭА.
Реализован этап 1. Нужен Python 3.9 или новее.
Зависимости: только стандартная библиотека и tkinter.

## Возможности этапа 1

- Графическое окно с историей ввода и вывода.
- Заголовок UNIX shell - demo-vfs содержит имя будущей VFS.
- Разбор одинарных и двойных кавычек, экранирования и пустых аргументов.
- Сообщения о неизвестной команде, неверных аргументах и ошибках кавычек.
- Заглушки ls и cd, команда exit.

На этом этапе VFS ещё не загружается. Имя demo-vfs является настройкой
в src/constants.py. Изменение имени через параметры появится на этапе 2.
Команда cd пока не меняет путь: она выводит переданные аргументы.

## Структура

- src/gui.py: окно и обработка Enter.
- src/parser.py: разбор команд с помощью shlex.
- src/shell.py: выполнение команд через словарь COMMANDS.
- src/commands/repl.py: отдельная функция для каждой команды.
- src/result.py: результат команды и признак закрытия окна.
- src/constants.py: именованные настройки и ограничения.
- tests/: модульные тесты и проверки ограничений кода.
- examples/stage1.txt: команды для ручной демонстрации.

Остальные модули согласованной структуры добавляются на следующих этапах.
Пустая папка scripts предназначена для проверочных скриптов этапов 2–3.

## Подготовка на macOS

Все команды выполняются в терминале VS Code.

Если репозиторий ещё не клонирован:

~~~sh
git clone https://github.com/mikenaebski-ctrl/MaxVolkov.git
cd MaxVolkov
git remote -v
~~~

Для уже клонированного проекта открой его корневую папку и выполни:

~~~sh
git remote -v
git status
~~~

Адрес origin должен указывать на mikenaebski-ctrl/MaxVolkov.
Сохрани setup_stage1.py вне репозитория, например в Downloads.
Запусти его из корня клонированного репозитория:

~~~sh
python3 -B ~/Downloads/setup_stage1.py
~~~

Он создаёт файлы без перезаписи существующих и запускает тесты.
Скрипт не выполняет git-команды и не устанавливает зависимости.

## Проверка tkinter

~~~sh
python3 --version
python3 -c "import tkinter"
python3 -m tkinter
~~~

Последняя команда открывает тестовое окно Tk.
Если импорт не работает, используй сборку Python с поддержкой Tcl/Tk.
Для macOS можно установить официальный Python с python.org.
После установки выбери этот интерпретатор в VS Code:
Python: Select Interpreter.
Дополнительная информация: https://docs.python.org/3/library/tkinter.html

## Сборка и запуск

Компиляция и установка пакетов не требуются.
Из корня проекта:

~~~sh
sh run.sh
~~~

Или:

~~~sh
python3 -B -m src
~~~

На Windows:

~~~bat
run.bat
~~~

Или:

~~~bat
python -B -m src
~~~

На этапе 1 параметров командной строки нет.
Пути VFS и стартового скрипта появятся на этапе 2.

## Команды

| Команда | Аргументы | Результат |
| --- | --- | --- |
| ls | Любое количество строк | Имя команды и список аргументов |
| cd | Ноль или один путь | Имя команды и список аргументов |
| exit | Без аргументов | Закрытие окна |

ls пока не проверяет существование путей и не разбирает опции.
cd тоже не проверяет пути. Пустой аргумент сохраняется парсером.
Пустая строка не выполняет команду.
Имена команд чувствительны к регистру.

Подстановки переменных, конвейеры и перенаправления не реализованы.
Команды не передаются оболочке реальной ОС.
Символ # пока является обычным аргументом;
комментарии стартовых скриптов появятся на этапе 2.

## Тестирование

На macOS:

~~~sh
python3 -B -m unittest discover -s tests -v
~~~

На Windows:

~~~bat
python -B -m unittest discover -s tests -v
~~~

Тесты ядра не требуют tkinter и графического экрана.
Проверяются кавычки, экранирование, пустые аргументы, ошибки,
восстановление после ошибки и признак завершения.
tests/test_quality.py проверяет длины строк, функций и файлов,
число параметров, сложность, docstring и числа в сравнениях.
Формула сложности: 1 + ветвления + циклы + обработчики исключений
+ дополнительные логические альтернативы.

В этой поставке тесты не запускались в среде автора:
среда исполнения была недоступна. Установщик запускает их локально.
При провале тестов не выполняй коммит, сначала посмотри сообщение.

## Демонстрация

Открой окно и вводи строки из examples/stage1.txt по одной.
Это пока ручной сценарий, автоматического чтения файла нет.
Приглашение имеет вид student@demo-vfs:/$.

~~~text
student@demo-vfs:/$ ls
ls: []
student@demo-vfs:/$ ls "My Documents" file.txt
ls: ['My Documents', 'file.txt']
student@demo-vfs:/$ ls 'single quoted path'
ls: ['single quoted path']
student@demo-vfs:/$ ls ""
ls: ['']
student@demo-vfs:/$ cd
cd: []
student@demo-vfs:/$ cd "My Documents"
cd: ['My Documents']
student@demo-vfs:/$ cd ..
cd: ['..']
student@demo-vfs:/$ cd first second
error: cd: expected at most one path
student@demo-vfs:/$ missing
error: missing: command not found
student@demo-vfs:/$ ls "unfinished
error: parse: No closing quotation
student@demo-vfs:/$ ls
ls: []
student@demo-vfs:/$ exit now
error: exit: expected no arguments
student@demo-vfs:/$ exit
~~~

После корректного exit окно закрывается.
Проверь вручную заголовок, ввод по Enter и прокрутку истории.
Графическое окно автоматически в этой поставке не проверялось.

## Коммит этапа 1

После успешных тестов выполни из корня репозитория:

~~~sh
git remote -v
git status
git add .gitignore README.md run.sh run.bat
git add src/__init__.py src/__main__.py src/constants.py
git add src/errors.py src/result.py src/parser.py src/shell.py
git add src/gui.py src/commands/__init__.py src/commands/repl.py
git add tests/__init__.py tests/test_parser.py tests/test_shell.py
git add tests/test_quality.py examples/stage1.txt
git diff --cached --stat
git commit -m "feat(repl): add GUI shell with quoted args parser" \
  -m "Add ls and cd stubs, validated exit, and readable diagnostics." \
  -m "Add unit tests, source quality checks, and launch scripts."
git push -u origin HEAD
~~~

Архив поставки и setup_stage1.py должны оставаться вне репозитория.
.gitignore исключает ZIP, кеши Python, настройки редакторов и сборку.
Тестовых ZIP на этапе 1 нет.
С этапа 3 они будут создаваться tests/make_vfs.py во время тестов.

## Что объяснить на защите

1. Tkinter получает ввод по событию Enter.
2. shlex.split разбивает строку по правилам кавычек UNIX.
3. Словарь COMMANDS выбирает отдельную функцию команды.
4. CommandResult отделяет результат выполнения от интерфейса.
5. Ожидаемые ошибки отображаются в истории и не завершают приложение.
6. Цикл Tkinter выполняет роль REPL: чтение, выполнение, вывод.

Пример: cd "My Documents" передаёт один путь с пробелом.
Обычный split разделил бы его на два аргумента.
