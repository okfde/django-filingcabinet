import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fc_project.settings")

from django.conf import settings  # noqa

from celery import Celery  # noqa

app = Celery("filingcabinet")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
