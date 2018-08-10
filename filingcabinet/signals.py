from django.db.models import signals
from django.dispatch import receiver

from . import get_document_model

Document = get_document_model()


@receiver(signals.post_save, sender=Document, dispatch_uid="document_created")
def document_created(instance=None, created=False, **kwargs):
    if created and kwargs.get('raw', False):
        return
    if not created:
        return

    from .tasks import process_document
    process_document.delay(instance.pk)
