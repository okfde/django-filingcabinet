from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = True
ALLOWED_HOSTS = ["*"]

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
]

FILINGCABINET_DOCUMENT_MODEL = "filingcabinet.Document"
FILINGCABINET_DOCUMENTCOLLECTION_MODEL = "filingcabinet.DocumentCollection"
FILINGCABINET_MEDIA_PUBLIC_PREFIX = "docs"
FILINGCABINET_MEDIA_PRIVATE_PREFIX = "docs-private"


MIDDLEWARE = [
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
        "DIRS": [BASE_DIR / "fc_project/templates"],
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

# Random secret key

SECRET_KEY = 'hTuFaTK;N3>hgE9@"*=[mY@)Nk[6g(PEMbOnP?&2@QyyCaGDjw'

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
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

TESSERACT_DATA_PATH = "/usr/local/share/tessdata"
