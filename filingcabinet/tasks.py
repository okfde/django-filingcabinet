from celery import shared_task

from . import get_document_model

Document = get_document_model()


@shared_task(acks_late=True, time_limit=5 * 60)
def process_document_task(doc_pk):
    from .services import process_document

    try:
        doc = Document.objects.get(pk=doc_pk)
    except Document.DoesNotExist:
        return None
    process_document(doc)


@shared_task(acks_late=True, time_limit=5 * 60)
def process_pages_task(doc_pk, page_numbers=None, task_page_limit=None):
    from .services import process_pages

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
    from .services import fix_file_paths

    try:
        doc = Document.objects.get(pk=doc_pk)
    except Document.DoesNotExist:
        return None
    fix_file_paths(doc)
    doc.pending = False
    doc.save()


@shared_task(acks_late=True, time_limit=5 * 60)
def publish_document(doc_pk, public=True):
    try:
        doc = Document.objects.get(pk=doc_pk)
    except Document.DoesNotExist:
        return None
    if doc.pending:
        return
    if public != doc.public:
        doc.public = public
        doc.pending = True
        doc.save()
        doc._move_file()
        doc.save()
        files_moved_task.delay(doc.pk)


@shared_task(acks_late=True, time_limit=5 * 60)
def detect_tables_document_task(doc_pk):
    from .services import detect_tables_on_doc

    try:
        doc = Document.objects.get(pk=doc_pk)
    except Document.DoesNotExist:
        return None
    detect_tables_on_doc(doc)
