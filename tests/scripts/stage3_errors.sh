#!/bin/sh
# Ошибки загрузки VFS: каждый вариант выводит сообщение, окно остаётся
set -eu
. "$(dirname "$0")/_vfs_env.sh"
for name in none.zip not_a_zip.zip truncated.zip corrupt.zip unsafe.zip clash.zip; do
  echo "== $name =="
  sh run.sh --vfs "$VFS_DIR/$name" --script examples/stage3_vfs_info.txt
done
echo "== каталог вместо файла =="
sh run.sh --vfs "$VFS_DIR" --script examples/stage3_vfs_info.txt
