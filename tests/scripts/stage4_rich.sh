#!/bin/sh
# Команды этапа 4 и общий скрипт всех команд на rich.zip
set -eu
. "$(dirname "$0")/_vfs_env.sh"
echo "== rich.zip, команды этапа 4 =="
sh run.sh --vfs "$VFS_DIR/rich.zip" --script examples/stage4_commands.txt
echo "== rich.zip, все команды этапов 1-4 =="
sh run.sh --vfs "$VFS_DIR/rich.zip" --script examples/all_commands.txt
