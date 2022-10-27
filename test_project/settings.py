import random
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

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
    "test_project.app",
]

FILINGCABINET_DOCUMENT_MODEL = "app.Document"
FILINGCABINET_DOCUMENTCOLLECTION_MODEL = "app.DocumentCollection"
FILINGCABINET_MEDIA_PUBLIC_PREFIX = "docs"
FILINGCABINET_MEDIA_PRIVATE_PREFIX = "docs-private"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "tests" / "testdata"
STATIC_ROOT = BASE_DIR / "static"

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "test_project.urls"

# FIXTURE_DIRS = [os.path.join(test_dir, 'fixtures'), ]

SITE_ID = 1

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [BASE_DIR / "fc_project" / "templates"],
        "OPTIONS": {
            "debug": True,
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

STATIC_URL = "/static/"
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

FRONTEND_BUILD_DIR = BASE_DIR / "build"
STATICFILES_DIRS = [FRONTEND_BUILD_DIR]

# Random secret key

key_chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
SECRET_KEY = "".join([random.SystemRandom().choice(key_chars) for i in range(50)])

# Logs all newsletter app messages to the console
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "newsletter": {
            "handlers": ["console"],
            "propagate": True,
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

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = CELERY_TASK_ALWAYS_EAGER
