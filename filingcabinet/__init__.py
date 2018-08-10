from django.apps import apps as django_apps
from django.core.exceptions import ImproperlyConfigured

from .settings import (
    FILINGCABINET_DOCUMENT_MODEL,
    FILINGCABINET_DOCUMENTCOLLECTION_MODEL
)


__version__ = '0.0.1'


def get_document_model():
    return get_model(FILINGCABINET_DOCUMENT_MODEL)


def get_documentcollection_model():
    return get_model(FILINGCABINET_DOCUMENTCOLLECTION_MODEL)


def get_model(model_name):
    """
    Return the User model that is active in this project.
    """
    try:
        return django_apps.get_model(
            model_name,
            require_ready=False
        )
    except ValueError:
        raise ImproperlyConfigured(
            "setting must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "setting refers to model '%s' that has not been installed" % (
                model_name
            )
        )
