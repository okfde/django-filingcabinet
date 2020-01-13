import os
import logging
import json

from django.core.files.base import ContentFile
from django.conf import settings

from .models import (
    Page, PageAnnotation,
    get_page_filename, get_page_annotation_filename
)
from .pdf_utils import PDFProcessor, crop_image, draw_highlights

logger = logging.getLogger(__name__)


def get_copy_func(doc):
    def copy_func(filename):
        return doc.get_writeable_file()

    return copy_func


def get_pdf_processor(doc):
    config = {
        'TESSERACT_DATA_PATH': settings.TESSERACT_DATA_PATH
    }
    pdf_path = doc.get_file_path()
    return PDFProcessor(
        pdf_path, copy_func=get_copy_func(doc),
        language=doc.language, config=config
    )


def process_document(doc):
    logger.info('Processing document %s', doc.id)
    pdf = get_pdf_processor(doc)
    doc.num_pages = pdf.num_pages
    doc.file_size = os.path.getsize(doc.get_file_path())
    doc.save()

    queue_missing_pages(doc)


def queue_missing_pages(doc):
    from .tasks import process_pages_task

    all_pages = set(range(1, doc.num_pages + 1))

    existing_pages = Page.objects.filter(
        document=doc, pending=False
    ).values_list('number', flat=True)

    missing_pages = list(all_pages - set(existing_pages))
    missing_pages.sort()

    logger.info(
        'Queueing processing of %s pages: %s',
        len(missing_pages), missing_pages
    )

    if not missing_pages:
        doc.pending = False
        doc.save()
        return

    process_pages_task.delay(
        doc.id, page_numbers=missing_pages, task_page_limit=20
    )


def process_pages(doc, page_numbers=None, task_page_limit=None):
    if page_numbers is None:
        page_numbers = list(range(1, doc.num_pages + 1))

    # Remove existing non-pending page numbers
    existing_pages = Page.objects.filter(
        document=doc, pending=False
    ).values_list('number', flat=True)
    page_numbers = list(set(page_numbers) - set(existing_pages))
    page_numbers.sort()

    if task_page_limit is None:
        process_page_numbers = page_numbers
    else:
        process_page_numbers = page_numbers[:task_page_limit]

    logger.info('Processing %s pages of doc %s', process_page_numbers, doc.id)
    pdf = get_pdf_processor(doc)

    for page_number, image in pdf.get_images(pages=process_page_numbers):
        process_page(doc, pdf, page_number, image)

    logger.info(
        'Processing %s pages done of doc %s',
        process_page_numbers, doc.id
    )
    # Check if doc is done
    done_pages = Page.objects.filter(document=doc, pending=False).count()
    if done_pages == doc.num_pages:
        logger.info('Processing pages of doc %s complete', doc.id)
        doc.pending = False
        doc.save()
    else:
        queue_missing_pages(doc)


def process_page(doc, pdf, page_number, image):
    logger.info('Getting text for page %s of doc %s', page_number, doc.id)
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
        text = pdf.get_text_for_page(page_number, image)
        page.content = text
    page.width = dims[0]
    page.height = dims[1]
    logger.info('Making thumbnails page %s of doc %s', page_number, doc.id)
    make_thumbnails(page, image)
    page.pending = False
    page.save()
    logger.info('Processing page %s of doc %s complete', page_number, doc.id)


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
    transform_func = None
    if annotation.highlight:
        highlights = json.loads(annotation.highlight)
        if highlights:
            transform_func = draw_highlights(highlights)

    image_bytes = crop_image(
        annotation.page.image.path,
        annotation.left, annotation.top, annotation.width, annotation.height,
        transform_func=transform_func
    )
    annotation.image.save(
        'page_annotation.png',
        ContentFile(image_bytes),
        save=False
    )


def fix_file_paths(doc):
    pages = Page.objects.filter(document=doc)
    for page in pages:
        fix_file_paths_for_page(page)


def fix_file_paths_for_page(page):
    changed = False
    for size_name, width in (('original', -1),) + Page.SIZES:
        if size_name == 'original':
            field_file = page.image
        else:
            field_file = getattr(page, 'image_%s' % size_name)
        real_filename = get_page_filename(page, 'page.png', size=size_name)
        if real_filename != field_file.name:
            field_file.name = real_filename
            changed = True
    if changed:
        page.save()

    annotations = PageAnnotation.objects.filter(page=page)
    for annotation in annotations:
        annotation.page = page
        fix_file_paths_for_pageannotation(annotation)


def fix_file_paths_for_pageannotation(annotation):
    filename = get_page_annotation_filename(annotation, 'annotation.png')
    if annotation.image and filename != annotation.image.name:
        annotation.image.name = filename
        annotation.save()
