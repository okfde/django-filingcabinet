from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FilingCabinetConfig(AppConfig):
    name = "filingcabinet"
    verbose_name = _("Filing Cabinet")
