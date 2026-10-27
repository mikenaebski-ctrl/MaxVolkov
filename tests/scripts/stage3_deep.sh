#!/bin/sh
# VFS глубиной 4 уровня и общий скрипт всех команд
set -eu
. "$(dirname "$0")/_vfs_env.sh"
echo "== deep.zip =="
sh run.sh --vfs "$VFS_DIR/deep.zip" --script examples/stage3_vfs_info.txt
echo "== deep.zip, все команды =="
sh run.sh --vfs "$VFS_DIR/deep.zip" --script examples/stage3_all_commands.txt
