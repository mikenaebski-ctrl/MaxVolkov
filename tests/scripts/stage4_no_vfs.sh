#!/bin/sh
# Команды без VFS и после неудачной загрузки: ошибки no VFS loaded
set -eu
. "$(dirname "$0")/_vfs_env.sh"
echo "== без --vfs =="
sh run.sh --script examples/stage4_commands.txt
echo "== not_a_zip.zip =="
sh run.sh --vfs "$VFS_DIR/not_a_zip.zip" --script examples/stage4_commands.txt
