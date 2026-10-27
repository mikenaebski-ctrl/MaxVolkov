#!/bin/sh
# Оба параметра вместе и ошибочные варианты
set -eu
cd "$(dirname "$0")/../.."
echo "== --vfs и --script =="
sh run.sh --vfs "demo.zip" --script examples/stage2_basic.txt
echo "== несуществующий скрипт (ошибка в окне) =="
sh run.sh --script "no/such/script.txt"
echo "== неизвестный параметр (ошибка argparse, код 2) =="
sh run.sh --bogus || echo "exit code: $?"
echo "== --vfs без значения (ошибка argparse, код 2) =="
sh run.sh --vfs || echo "exit code: $?"
