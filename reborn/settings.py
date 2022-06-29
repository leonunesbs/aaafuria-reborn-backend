
from pathlib import Path

import django_heroku
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = []


INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',

    'graphene_django',
    'storages',

    'core',
    'ecommerce',
    'bank',

    'partnerships',

    # Refactored apps
    'activities',
    'memberships',
    'members',
    'store'
]

X_FRAME_OPTIONS = 'SAMEORIGIN'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'reborn.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'reborn.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
    {
        'NAME': 'reborn.validators.PasswordLengthValidator',
    },
    {
        'NAME': 'reborn.validators.PasswordOnlyNumericValidator',
    }
]


LANGUAGE_CODE = 'pt-br'

LANGUAGES = [
    ('pt-br', 'Português'),
    ('en', 'English')
]

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_L10N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


GRAPHENE = {
    "SCHEMA": "reborn.schema.schema",
    "MIDDLEWARE": [
        "graphql_jwt.middleware.JSONWebTokenMiddleware",
    ],
}

AUTHENTICATION_BACKENDS = [
    "graphql_jwt.backends.JSONWebTokenBackend",
    "django.contrib.auth.backends.ModelBackend",
]


CORS_ALLOW_ALL_ORIGINS = True


STRIPE_API_KEY = config('STRIPE_API_KEY')
STRIPE_API_TEST_KEY = config('STRIPE_API_TEST_KEY')

CORE_WEBHOOK_SECRET = config('CORE_WEBHOOK_SECRET', default='')
ECOMMERCE_WEBHOOK_SECRET = config(
    'ECOMMERCE_WEBHOOK_SECRET', default=' ')
BANK_WEBHOOK_SECRET = config('BANK_WEBHOOK_SECRET', default='')
EVENTOS_WEBHOOK_SECRET = config('EVENTOS_WEBHOOK_SECRET', default='')
MEMBERSHIPS_WEBHOOK_SECRET = config('MEMBERSHIPS_WEBHOOK_SECRET', default='')


BITLY_LOGIN = config('BITLY_LOGIN')
BITLY_API_KEY = config('BITLY_API_KEY')


# aws settings
AWS_ACCESS_KEY_ID = config('AWS_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET')
AWS_STORAGE_BUCKET_NAME = config('S3_BUCKET')
AWS_S3_REGION_NAME = 'sa-east-1'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_DEFAULT_ACL = 'public-read'

# s3 static settings
AWS_LOCATION = 'static'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
STATICFILES_STORAGE = 'reborn.storage_backends.StaticStorage'


# s3 public media settings
PUBLIC_MEDIA_LOCATION = 'media'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/'
DEFAULT_FILE_STORAGE = 'reborn.storage_backends.PublicMediaStorage'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')


# Configure Django App for Heroku.
django_heroku.settings(locals(), staticfiles=False)
