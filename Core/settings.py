"""
Settings project SMDPD (Sistema Managemen Dadus Membru Partidu PLP).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# Seguru tuir defeitu: DEBUG la'ós (tenke define DJANGO_DEBUG=True iha .env ba dezenvolvimentu)
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
	if DEBUG:
		SECRET_KEY = 'dev-only-key-troka-iha-produksaun'  # nosec B105 - deit ba DEBUG/dezenvolvimentu
	else:
		raise RuntimeError('DJANGO_SECRET_KEY tenke iha se DEBUG=False. Ba dezenvolvimentu: kopia .env.example ba .env (DJANGO_DEBUG=True).')

CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if h.strip()]

INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'django.contrib.humanize',
	'crispy_forms',
	'crispy_bootstrap4',
	'rest_framework',
	'main.apps.MainConfig',
	'custom.apps.CustomConfig',
	'config.apps.ConfigConfig',
	'user.apps.UserConfig',
	'membro.apps.MembroConfig',
	'notif.apps.NotifConfig',
	'anunsiu.apps.AnunsiuConfig',
	'eventu.apps.EventuConfig',
	'kuota.apps.KuotaConfig',
	'report.apps.ReportConfig',
]

MIDDLEWARE = [
	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'config.middleware.SeguransaMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Core.urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
				'config.context_processors.nav_context',
			],
		},
	},
]

WSGI_APPLICATION = 'Core.wsgi.application'

if os.environ.get('DB_ENGINE', 'sqlite') == 'mysql':
	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.mysql',
			'NAME': os.environ.get('DB_NAME', 'smdpd'),
			'USER': os.environ.get('DB_USER', 'root'),
			'PASSWORD': os.environ.get('DB_PASSWORD', ''),
			'HOST': os.environ.get('DB_HOST', 'localhost'),
			'PORT': os.environ.get('DB_PORT', '3306'),
		}
	}
else:
	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.sqlite3',
			'NAME': BASE_DIR / 'db.sqlite3',
		}
	}

AUTH_PASSWORD_VALIDATORS = [
	{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
	{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
	{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
	{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dili'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# MEDIA = file públiku (logo orgaun). Fotu membru rai iha PRIVATE_MEDIA_ROOT (la públiku): hatudu liu husi view ho login no área.
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
PRIVATE_MEDIA_ROOT = os.path.join(BASE_DIR, 'private_media')

# Limite upload no form (proteje husi file boot liu / field barak liu)
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o640
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o750

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap4'
CRISPY_TEMPLATE_PACK = 'bootstrap4'

LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'login'

from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
	message_constants.DEBUG: 'debug',
	message_constants.INFO: 'info',
	message_constants.SUCCESS: 'success',
	message_constants.WARNING: 'warning',
	message_constants.ERROR: 'danger',
}

REST_FRAMEWORK = {
	'DEFAULT_AUTHENTICATION_CLASSES': [
		'rest_framework.authentication.SessionAuthentication',
	],
	'DEFAULT_PERMISSION_CLASSES': [
		'rest_framework.permissions.IsAuthenticated',
	],
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ───────── Seguransa login no sesaun ─────────
def _env_bool(nome, defeitu):
	return os.environ.get(nome, str(defeitu)) == 'True'


# Sesaun: sai automátiku bainhira la uza (minutu), no bainhira taka browser
SESSION_IDLE_MINUTES = int(os.environ.get('SESSION_IDLE_MINUTES', '120'))
SESSION_COOKIE_AGE = SESSION_IDLE_MINUTES * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Proxy (nginx/PythonAnywhere): fiar header X-Forwarded-* ba IP no HTTPS
TRUST_PROXY = _env_bool('DJANGO_TRUST_PROXY', False)
if TRUST_PROXY:
	SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 2FA obrigatóriu ba Admin, Presidente no Sekretaria Nasionál (aktiva iha produksaun ho DJANGO_2FA_WAJIBA=True)
SMDPD_2FA_WAJIBA = _env_bool('DJANGO_2FA_WAJIBA', False)

# URL admin Django bele muda (ez. DJANGO_ADMIN_URL=gestaun-rahasia/)
ADMIN_URL = os.environ.get('DJANGO_ADMIN_URL', 'admin/').strip('/') + '/'

if not DEBUG:
	SESSION_COOKIE_SECURE = True
	CSRF_COOKIE_SECURE = True
	SECURE_SSL_REDIRECT = _env_bool('DJANGO_SSL_REDIRECT', True)
	SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', '31536000'))
	SECURE_HSTS_INCLUDE_SUBDOMAINS = True
	SECURE_HSTS_PRELOAD = False
