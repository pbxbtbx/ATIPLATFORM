#!/bin/sh
set -eu
cd /workspace/ATIPLATFORM
if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi
.venv/bin/python -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py check
