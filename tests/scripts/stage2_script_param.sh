#!/bin/sh
# Параметр --script: скрипт без ошибок, затем со всеми ошибками
set -eu
cd "$(dirname "$0")/../.."
echo "== --script (корректный) =="
sh run.sh --script examples/stage2_basic.txt
echo "== --script (с ошибками, завершается exit) =="
sh run.sh --script examples/stage2_errors.txt
