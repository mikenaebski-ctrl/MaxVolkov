#!/bin/sh
# Параметр --vfs: имя VFS попадает в заголовок окна
set -eu
cd "$(dirname "$0")/../.."
echo "== --vfs =="
sh run.sh --vfs "some/path/training.zip"
