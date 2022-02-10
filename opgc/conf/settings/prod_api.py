import os
from conf.settings.base import *


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
IS_PROD = True

ALLOWED_HOSTS = ['OPGC_ALLOWED_HOSTS']

# Gihub api auth token
OPGC_TOKEN = 'OPGG_GITHUB_TOKEN'
GITHUB_API_HEADER = {'Authorization': f'token {OPGC_TOKEN}'}

# 임시
CORS_ORIGIN_ALLOW_ALL = True
# CORS_ALLOW_CREDENTIALS = True
# CORS_ALLOWED_ORIGINS = []

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware'
]

ROOT_URLCONF = 'conf.urls.api'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'opgc.wsgi.application'

#########################################
#           DataBase
#########################################
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'opgcdb',
        'OPTIONS': {
            'read_default_file': 'OPGC_DB_CONF',
            'charset': 'utf8mb4',
            'init_command': 'set collation_connection=utf8mb4_unicode_ci; SET default_storage_engine=INNODB; SET SQL_MODE=STRICT_TRANS_TABLES;',
        },
        'CONN_MAX_AGE': 600,
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

#########################################
#           센트리 리포팅
#########################################
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="OPGC_SENTRY_REPORTING",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)

#########################################
#           슬랙 채널
#########################################
SLACK_CHANNEL_JOINED_USER = 'slack_channel_joined_user_key'
SLACK_CHANNEL_CRONTAB = 'slack_channel_crontab'

#########################################
#      Time Zone and language
#########################################
# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
"""
    When USE_TZ is False, this is the time zone in which Django will store all datetimes. 
    When USE_TZ is True, this is the default time zone that Django will use to display 
    datetimes in templates and to interpret datetimes entered in forms.
"""
USE_TZ = False  # DB에는 UTC로 저장
USE_I18N = True
USE_L10N = True
TIME_ZONE = 'Asia/Seoul'
LANGUAGE_CODE = 'ko-kr'


#########################################
#           기타 등등
#########################################
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

PROFILE_IMAGE_DIR = 'PROFILE_IMAGE_PROD_PATH'

# CKEditor
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
    }
}


# ===========================================================
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "OPGC_REDIS_DEFAULT_HOST",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PARSER_CLASS": "redis.connection.HiredisParser",
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "IGNORE_EXCEPTIONS": True,
        }
    }
}

INSTALLED_APPS += ['cacheops']

CACHEOPS_LRU = True
CACHEOPS_REDIS = "OPGC_REDIS_CACHEOPS_HOST" # local redis

CACHEOPS_DEFAULTS = {
    'timeout': 60 * 60 * 1, # 1시간
    'ops': 'all',
    'cache_on_save': False
}

CACHEOPS = {
    'githubs.*': {},
    'ranks.*': {},
    'notices.*': {},
}
