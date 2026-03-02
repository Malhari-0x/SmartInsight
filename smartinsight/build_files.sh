#!/bin/bash
set -o errexit

python -m pip install --break-system-packages --upgrade pip
python -m pip install --break-system-packages -r requirements.txt
python manage.py collectstatic --noinput
