# config/settings_production.py
# Herda tudo do settings.py base e sobrescreve apenas o necessário para produção

from .settings import *
import dj_database_url

# ─────────────────────────────────────────────
#  SEGURANÇA
# ─────────────────────────────────────────────
DEBUG = False

ALLOWED_HOSTS = ['.onrender.com']

# ─────────────────────────────────────────────
#  BANCO DE DADOS
#  Substitui a config individual por DATABASE_URL
#  injetada automaticamente pelo Render
# ─────────────────────────────────────────────
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ─────────────────────────────────────────────
#  ARQUIVOS ESTÁTICOS (WhiteNoise)
#  Serve os estáticos sem precisar de Nginx
# ─────────────────────────────────────────────
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ─────────────────────────────────────────────
#  ARQUIVOS DE MÍDIA
#  Atenção: o Render não persiste arquivos em disco
#  no plano gratuito. Se o projeto usar upload de
#  imagens futuramente, será necessário usar um
#  serviço externo como Cloudinary ou AWS S3.
#  Por ora, a config abaixo mantém compatibilidade.
# ─────────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─────────────────────────────────────────────
#  SEGURANÇA HTTPS
# ─────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
