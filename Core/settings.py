"""
Settings project SMDPD (Sistema Managemen Dadus Membru Partidu PLP).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
	if DEBUG:
		SECRET_KEY = 'dev-only-key-troka-iha-produksaun'
	else:
		raise RuntimeError('DJANGO_SECRET_KEY tenke iha se DEBUG=False')

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
	'config.middleware.TrokaPasswordMiddleware',
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
	{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
	{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
	{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dili'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

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

# Cookie no header seguransa báziku
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = 'DENY'
if not DEBUG:
	SESSION_COOKIE_SECURE = True
	CSRF_COOKIE_SECURE = True
