#!/usr/bin/env bash
# build.sh — executado pelo Render a cada deploy
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
python manage.py populate_demo
