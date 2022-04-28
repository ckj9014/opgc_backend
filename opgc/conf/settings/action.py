import os
from pathlib import Path
from conf.settings.base import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
IS_PROD = False

ALLOWED_HOSTS = ['*', 'localhost:8000', '127.0.0.1', 'localhost']

# Gihub api auth token
OPGC_TOKEN = 'OPGC_GITHUB_TOKEN'
GITHUB_API_HEADER = {'Authorization': f'token {OPGC_TOKEN}'}

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
#     GitHub Action 데이터 베이스 세팅
#########################################
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'opgc_ci_db',
        'USER': 'root',
        'HOST': '127.0.0.1',
        'PASSWORD': 'ci_user_pw123',
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
#           슬랙 채널
#########################################
SLACK_CHANNEL_JOINED_USER = None
SLACK_CHANNEL_CRONTAB = None

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

STATIC_URL = 'static'
STATIC_ROOT = ''
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# CKEditor
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
    }
}
