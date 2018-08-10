from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class FilingCabinetConfig(AppConfig):
    name = 'filingcabinet'
    verbose_name = _('Filing Cabinet')

    def ready(self):
        import .signals  # noqa
