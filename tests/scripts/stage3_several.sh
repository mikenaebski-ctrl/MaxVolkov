#!/bin/sh
# VFS с несколькими файлами и бинарным файлом (base64)
set -eu
. "$(dirname "$0")/_vfs_env.sh"
echo "== several.zip =="
sh run.sh --vfs "$VFS_DIR/several.zip" --script examples/stage3_vfs_info.txt
echo "== binary.zip =="
sh run.sh --vfs "$VFS_DIR/binary.zip" --script examples/stage3_vfs_info.txt
