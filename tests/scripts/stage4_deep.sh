#!/bin/sh
# Навигация по VFS глубиной 4 уровня
set -eu
. "$(dirname "$0")/_vfs_env.sh"
echo "== deep.zip =="
sh run.sh --vfs "$VFS_DIR/deep.zip" --script examples/stage4_deep.txt
