#!/bin/bash
set -e

echo "=== ${INSTITUICAO_NOME:-Sistema} - Iniciando ambiente ==="

: "${SECRET_KEY:?SECRET_KEY não definida no ambiente}"
: "${DB_PASSWORD:?DB_PASSWORD não definida no ambiente}"

echo "Aguardando banco de dados..."
while ! python -c "
import psycopg2, os, sys, socket

host = os.environ.get('DB_HOST', 'db')

# Tenta resolver o nome para IP (contorna limitação de DNS do Podman no Windows)
try:
    host = socket.gethostbyname(host)
except Exception:
    pass

try:
    psycopg2.connect(
        dbname=os.environ.get('DB_NAME', 'varrevila'),
        user=os.environ.get('DB_USER', 'varrevila_user'),
        password=os.environ['DB_PASSWORD'],
        host=host,
        port=os.environ.get('DB_PORT', '5432'),
        connect_timeout=3,
    )
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "  banco ainda não disponível, aguardando 2s..."
    sleep 2
done
echo "Banco de dados pronto!"

echo "Aplicando migrações..."
python manage.py migrate --noinput

echo "Criando dados de demonstração..."
LOAD_DEMO_DATA=1 python manage.py populate_demo

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo ""
echo "=========================================="
echo "  ${INSTITUICAO_NOME:-Sistema} - Sistema pronto!"
echo "  Acesse: http://localhost:8000"
echo ""
echo "  Contas de demonstração:"
echo "  Admin:      admin / admin123"
echo "  Voluntário: voluntario1 / voluntario123"
echo "  Admin Django: http://localhost:8000/admin/"
echo "=========================================="

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
