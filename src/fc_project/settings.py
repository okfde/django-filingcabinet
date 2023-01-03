import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key


def env(name, default=None):
    return os.environ.get(name, default)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.getenv("DEBUG", "0") == "1"
ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = ["http://localhost:8080"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.auth",
    "django.contrib.messages",
    "django.contrib.admin",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "taggit",
    "django_json_widget",
    "filingcabinet",
    "fcdocs_annotate.annotation.apps.AnnotationConfig",
]

FILINGCABINET_DOCUMENT_MODEL = "filingcabinet.Document"
FILINGCABINET_DOCUMENTCOLLECTION_MODEL = "filingcabinet.DocumentCollection"
FILINGCABINET_MEDIA_PUBLIC_PREFIX = "docs"
FILINGCABINET_MEDIA_PRIVATE_PREFIX = "docs-private"
FILINGCABINET_MEDIA_PRIVATE_INTERNAL = "/protected/"
FILINGCABINET_ENABLE_WEBP = False


MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "fc_project.urls"

# FIXTURE_DIRS = [os.path.join(test_dir, 'fixtures'), ]

SITE_ID = 1

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [BASE_DIR / "src" / "fc_project/templates"],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Enable time-zone support
USE_TZ = True
TIME_ZONE = "UTC"

# Required for django-webtest to work
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

FRONTEND_BUILD_DIR = BASE_DIR / "build"
STATICFILES_DIRS = [FRONTEND_BUILD_DIR]

MEDIA_URL = "/media/"
MEDIA_ROOT = env("MEDIA_ROOT", BASE_DIR / "data")

# Random secret key

SECRET_KEY = env("SECRET_KEY", "not-secret" if DEBUG else get_random_secret_key())

# Logs all newsletter app messages to the console
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        }
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "": {"handlers": ["console"], "level": "WARNING"},
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PAGINATION_CLASS": "filingcabinet.api_utils.CustomLimitOffsetPagination",
    "PAGE_SIZE": 50,
}

CELERY_TASK_ALWAYS_EAGER = bool(int(env("CELERY_TASK_ALWAYS_EAGER", "1")))
CELERY_TASK_EAGER_PROPAGATES = CELERY_TASK_ALWAYS_EAGER
CELERY_BROKER_URL = env("CELERY_BROKER_URL")

TESSERACT_DATA_PATH = None
