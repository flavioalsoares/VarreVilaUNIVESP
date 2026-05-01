from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'users',
    'events',
    'impact',
    'dashboard',
    'core',
    'public',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.instituicao',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'varrevila'),
        'USER': os.environ.get('DB_USER', 'varrevila_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'varrevila_pass'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'users.CustomUser'

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/sistema/'
LOGOUT_REDIRECT_URL = '/users/login/'

# ─────────────────────────────────────────────
#  VARIÁVEIS INSTITUCIONAIS
#  Para alterar o nome da organização, edite
#  as variáveis abaixo ou defina as variáveis
#  de ambiente correspondentes.
# ─────────────────────────────────────────────
INSTITUICAO_NOME = os.environ.get('INSTITUICAO_NOME', 'Nome Projeto')
INSTITUICAO_SUBTITULO = os.environ.get('INSTITUICAO_SUBTITULO', 'Limpeza Comunitária')
INSTITUICAO_SLOGAN = os.environ.get('INSTITUICAO_SLOGAN', 'Movimento Popular de Limpeza Urbana em São Paulo')
INSTITUICAO_EMAIL = os.environ.get('INSTITUICAO_EMAIL', 'contato@varrevila.org')
INSTITUICAO_FACEBOOK = os.environ.get('INSTITUICAO_FACEBOOK', 'https://www.facebook.com/varrevila/')
INSTITUICAO_ANO_FUNDACAO = os.environ.get('INSTITUICAO_ANO_FUNDACAO', '2018')
INSTITUICAO_APROVA_1 = os.environ.get('INSTITUICAO_APROVA_1', 'Aprovador 1')
INSTITUICAO_APROVA_2 = os.environ.get('INSTITUICAO_APROVA_2', 'Aprovador 2')
INSTITUICAO_APROVA_3 = os.environ.get('INSTITUICAO_APROVA_3', 'Aprovador 3')
