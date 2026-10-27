#!/bin/sh
# Общая подготовка: временный каталог с тестовыми архивами (в git их нет)
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VFS_DIR="$(mktemp -d)"
trap 'rm -rf "$VFS_DIR"' EXIT
python3 -B "$ROOT/tests/make_vfs.py" "$VFS_DIR" > /dev/null
cd "$ROOT"
