#!/bin/sh
# mv на rich.zip и общий скрипт всех команд
set -eu
. "$(dirname "$0")/_vfs_env.sh"
echo "== rich.zip, команда mv =="
sh run.sh --vfs "$VFS_DIR/rich.zip" --script examples/stage5_mv.txt
echo "== rich.zip, все команды этапов 1-5 =="
sh run.sh --vfs "$VFS_DIR/rich.zip" --script examples/all_commands.txt
