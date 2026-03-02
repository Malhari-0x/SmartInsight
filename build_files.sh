#!/bin/bash
set -o errexit

python -m pip install --break-system-packages --upgrade pip
python -m pip install --break-system-packages -r smartinsight/requirements.txt
cd smartinsight
python manage.py migrate --noinput
python manage.py seed_demo_user --username "User" --password "User@1234"
python manage.py collectstatic --noinput
