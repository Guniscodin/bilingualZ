#!/usr/bin/env sh
# Run Bilingualz natively on Linux/macOS from source.
#
# This is the "try it without rebooting into Windows" path: same engine, same
# UI, same JSON store - only the packaged .exe wrapper is missing.
#
# The venv is created with --system-site-packages on purpose: pywebview's GTK
# backend is PyGObject + WebKit2GTK, which are distro packages (python3-gi,
# gir1.2-webkit2-4.1). A normal venv would hide them.
#
#   Debian/Ubuntu: sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1
#   Fedora:        sudo dnf install python3-gobject gtk3 webkit2gtk4.1
#   Arch:          sudo pacman -S python-gobject gtk3 webkit2gtk-4.1
#
# On macOS no extra packages are needed (system WebKit is used).
set -e
cd "$(dirname "$0")"

PYTHON=${PYTHON:-python3}
VENV=${BILINGUALZ_VENV:-.venv-linux}

if [ ! -x "$VENV/bin/python" ]; then
    echo "Creating $VENV ..."
    "$PYTHON" -m venv --system-site-packages "$VENV"
fi

"$VENV/bin/python" -m pip install -q --upgrade pip
"$VENV/bin/python" -m pip install -q -e .
exec "$VENV/bin/python" run.py "$@"
