from celery import shared_task

from . import get_document_model
from .services import process_document, process_pages, fix_file_paths

Document = get_document_model()


@shared_task(acks_late=True, time_limit=5 * 60)
def process_document_task(doc_pk):
    try:
        doc = Document.objects.get(pk=doc_pk)
    except Document.DoesNotExist:
        return None
    process_document(doc)


@shared_task(acks_late=True, time_limit=5 * 60)
def process_pages_task(doc_pk, page_numbers=None, task_page_limit=None):
    try:
        doc = Document.objects.get(pk=doc_pk)
    except Document.DoesNotExist:
        return None
    process_pages(
        doc,
        page_numbers=page_numbers,
        task_page_limit=task_page_limit
    )


@shared_task(acks_late=True, time_limit=5 * 60)
def files_moved_task(doc_pk):
    try:
        doc = Document.objects.get(pk=doc_pk)
    except Document.DoesNotExist:
        return None
    fix_file_paths(doc)
