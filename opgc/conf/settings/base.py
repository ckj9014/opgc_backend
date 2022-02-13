# 배포 버전
RELEASE_VERSION = '2022.2.14'


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',

    'apps.users',
    'apps.githubs',
    'apps.reservations',
    'apps.ranks',
    'apps.notices',

    'corsheaders',
    'ckeditor'
]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'OPGC_SECRET_KEY'
