#!/bin/bash
set -o errexit

python -m pip install --break-system-packages --upgrade pip
python -m pip install --break-system-packages -r smartinsight/requirements.txt
cd smartinsight
python manage.py collectstatic --noinput
