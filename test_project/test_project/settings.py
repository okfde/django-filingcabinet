import os
import random

test_dir = os.path.dirname(__file__)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(test_dir, 'db.sqlite3'),
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'taggit',
    'django_json_widget',

    'filingcabinet',
    'test_project.app'
]

FILINGCABINET_DOCUMENT_MODEL = 'app.Document'
FILINGCABINET_DOCUMENTCOLLECTION_MODEL = 'app.DocumentCollection'
FILINGCABINET_MEDIA_PUBLIC_PREFIX = 'docs'
FILINGCABINET_MEDIA_PRIVATE_PREFIX = 'docs-private'


MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'test_project.urls'

# FIXTURE_DIRS = [os.path.join(test_dir, 'fixtures'), ]

SITE_ID = 1

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [os.path.join(test_dir, 'templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Enable time-zone support
USE_TZ = True
TIME_ZONE = 'UTC'

# Required for django-webtest to work
STATIC_URL = '/static/'

# Random secret key

key_chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
SECRET_KEY = ''.join([
    random.SystemRandom().choice(key_chars) for i in range(50)
])

# Logs all newsletter app messages to the console
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'newsletter': {
            'handlers': ['console'],
            'propagate': True,
        },
    },
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
}
