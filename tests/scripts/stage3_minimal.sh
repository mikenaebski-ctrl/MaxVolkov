#!/bin/sh
# VFS из одного файла и пустой архив
set -eu
. "$(dirname "$0")/_vfs_env.sh"
echo "== minimal.zip =="
sh run.sh --vfs "$VFS_DIR/minimal.zip" --script examples/stage3_vfs_info.txt
echo "== empty.zip =="
sh run.sh --vfs "$VFS_DIR/empty.zip" --script examples/stage3_vfs_info.txt
