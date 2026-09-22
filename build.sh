#!/usr/bin/env bash
# build.sh — executado pelo Render a cada deploy
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Dados de demonstração — o banco gratuito do Render é recriado a cada
# renovação e nasce vazio. O comando é idempotente: em deploy comum não
# duplica nada. Exige LOAD_DEMO_DATA=1, definida no render.yaml.
python manage.py populate_demo
