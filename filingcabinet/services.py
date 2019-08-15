import os

from django.core.files.base import ContentFile
from django.conf import settings

from .models import Page
from .pdf_utils import PDFProcessor, crop_image


def get_pdf_processor(doc):
    config = {
        'TESSERACT_DATA_PATH': settings.TESSERACT_DATA_PATH
    }
    pdf_path = doc.get_file_path()
    return PDFProcessor(pdf_path, language=doc.language, config=config)


def process_document(doc):
    from .tasks import process_pages_task

    pdf = get_pdf_processor(doc)
    doc.num_pages = pdf.num_pages
    doc.file_size = os.path.getsize(doc.get_file_path())
    doc.save()

    all_pages = set(range(1, doc.num_pages + 1))

    existing_pages = Page.objects.filter(
        document=doc,
        pending=False
    ).values_list('number', flat=True)

    missing_pages = list(all_pages - set(existing_pages))
    missing_pages.sort()

    process_pages_task.delay(
        doc.id, page_numbers=missing_pages, task_page_limit=100
    )


def process_pages(doc, page_numbers=None, task_page_limit=None):
    from .tasks import process_pages_task

    if page_numbers is None:
        page_numbers = list(range(1, doc.num_pages + 1))

    if task_page_limit is None:
        process_page_numbers = page_numbers
    else:
        process_page_numbers = page_numbers[:task_page_limit]

    pdf = get_pdf_processor(doc)

    for page_number, image in pdf.get_images(pages=process_page_numbers):
        process_page(doc, pdf, page_number, image)

    # Check if doc is done
    pending_pages = Page.objects.filter(document=doc, pending=True).count()
    if pending_pages == 0:
        doc.pending = False
        doc.save()

    if task_page_limit:
        remaining = page_numbers[task_page_limit:]
        if remaining:
            process_pages_task.delay(
                doc.id, page_numbers=remaining,
                task_page_limit=task_page_limit
            )


def process_page(doc, pdf, page_number, image):
    text = pdf.get_text_for_page(page_number, image)
    dims = image.size

    try:
        page = Page.objects.get(
            document=doc,
            number=page_number,
        )
    except Page.DoesNotExist:
        page = Page(
            document=doc, number=page_number,
            pending=True
        )

    if not page.pending:
        return

    if not page.corrected:
        page.content = text
    page.width = dims[0]
    page.height = dims[1]

    make_thumbnails(page, image)
    page.pending = False
    page.save()


def make_thumbnails(page, image):
    if page.image:
        page.image.delete(save=False)
    page.image.save(
        'page.png',
        ContentFile(image.make_blob('png')),
        save=False
    )
    for size_name, width in Page.SIZES:
        image.transform(resize='{}x'.format(width))
        field_file = getattr(page, 'image_%s' % size_name)
        if field_file:
            field_file.delete(save=False)
        field_file.save(
            'page.png',
            ContentFile(image.make_blob('png')),
            save=False
        )


def make_page_annotation(annotation):
    image_bytes = crop_image(
        annotation.page.image.path,
        annotation.left, annotation.top, annotation.width, annotation.height
    )
    annotation.image.save(
        'page_annotation.png',
        ContentFile(image_bytes),
        save=False
    )
