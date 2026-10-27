#!/bin/sh
# mv без VFS и после неудачной загрузки
set -eu
. "$(dirname "$0")/_vfs_env.sh"
echo "== без --vfs =="
sh run.sh --script examples/stage5_mv.txt
echo "== truncated.zip =="
sh run.sh --vfs "$VFS_DIR/truncated.zip" --script examples/stage5_mv.txt
