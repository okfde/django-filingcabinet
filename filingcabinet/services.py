import json
import logging
import os
import zipfile
from io import BytesIO
from pathlib import PurePath

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.text import slugify

try:
    import webp
except ImportError:
    webp = None
from PIL import Image as PILImage

from . import get_document_model
from .models import (
    CollectionDirectory,
    CollectionDocument,
    Page,
    PageAnnotation,
    get_page_annotation_filename,
    get_page_filename,
)
from .pdf_utils import PDFProcessor, crop_image, detect_tables, draw_highlights
from .tasks import convert_images_to_webp_task, process_document_task
from .utils import estimate_time

Document = get_document_model()


logger = logging.getLogger(__name__)


def get_copy_func(doc):
    def copy_func(filename):
        return doc.get_writeable_file()

    return copy_func


def get_pdf_processor(doc):
    config = {"TESSERACT_DATA_PATH": settings.TESSERACT_DATA_PATH}
    pdf_path = doc.get_file_path()
    return PDFProcessor(
        pdf_path, copy_func=get_copy_func(doc), language=doc.language, config=config
    )


def process_document(doc):
    if not doc.get_file_path():
        return
    logger.info("Processing document %s", doc.id)
    pdf = get_pdf_processor(doc)
    doc.num_pages = pdf.num_pages
    # TODO: make storage agnostic
    doc.file_size = os.path.getsize(doc.get_file_path())

    meta = pdf.get_meta()
    doc.properties.update(meta)
    if doc.title.endswith(".pdf"):
        if doc.properties.get("title"):
            doc.title = doc.properties["title"]
        else:
            doc.title = doc.title.rsplit(".pdf")[0]

    if not doc.slug and doc.title:
        doc.slug = slugify(doc.title)

    if not doc.outline:
        doc.outline = pdf.get_markdown_outline()

    detect_tables_on_doc(doc, save=False)

    doc.save()

    queue_missing_pages(doc)


def queue_missing_pages(doc):
    from .tasks import process_pages_task

    all_pages = set(range(1, doc.num_pages + 1))

    existing_pages = Page.objects.filter(document=doc, pending=False).values_list(
        "number", flat=True
    )

    missing_pages = list(all_pages - set(existing_pages))
    missing_pages.sort()

    logger.info(
        "Queueing processing of %s pages: %s", len(missing_pages), missing_pages
    )

    if not missing_pages:
        doc.pending = False
        doc.save()
        return

    process_pages_task.apply_async(
        args=[doc.id],
        kwargs={"page_numbers": missing_pages, "task_page_limit": 10},
        time_limit=max(60 + estimate_time(doc.file_size), 5 * 60),
    )


def process_pages(doc, page_numbers=None, task_page_limit=None):
    if page_numbers is None:
        page_numbers = list(range(1, doc.num_pages + 1))

    # Remove existing non-pending page numbers
    existing_pages = Page.objects.filter(document=doc, pending=False).values_list(
        "number", flat=True
    )
    page_numbers = list(set(page_numbers) - set(existing_pages))
    page_numbers.sort()

    if task_page_limit is None:
        process_page_numbers = page_numbers
    else:
        process_page_numbers = page_numbers[:task_page_limit]

    logger.info("Processing %s pages of doc %s", process_page_numbers, doc.id)
    pdf = get_pdf_processor(doc)

    timeout = estimate_time(doc.file_size)

    for page_number, image in pdf.get_images(
        pages=process_page_numbers, timeout=timeout
    ):
        process_page(doc, pdf, page_number, image)

    logger.info("Processing %s pages done of doc %s", process_page_numbers, doc.id)
    # Check if doc is done
    done_pages = Page.objects.filter(document=doc, pending=False).count()
    if done_pages == doc.num_pages:
        logger.info("Processing pages of doc %s complete", doc.id)
        doc.pending = False
        doc.save()
        if webp is not None:
            convert_images_to_webp_task.delay(doc.pk)
    else:
        queue_missing_pages(doc)


def process_page(doc, pdf, page_number, image):
    logger.info("Getting text for page %s of doc %s", page_number, doc.id)
    dims = image.size

    try:
        page = Page.objects.get(
            document=doc,
            number=page_number,
        )
    except Page.DoesNotExist:
        page = Page(document=doc, number=page_number, pending=True)

    if not page.pending:
        return

    if not page.corrected:
        text = pdf.get_text_for_page(page_number, image)
        page.content = text
    page.width = dims[0]
    page.height = dims[1]
    logger.info("Making thumbnails page %s of doc %s", page_number, doc.id)
    make_thumbnails(page, image)
    page.pending = False
    page.save()
    logger.info("Processing page %s of doc %s complete", page_number, doc.id)


def make_thumbnails(page, image):
    if page.image:
        page.image.delete(save=False)
    page.image.save("page.png", ContentFile(image.make_blob("png")), save=False)
    for size_name, width in Page.SIZES:
        image.transform(resize="{}x".format(width))
        field_file = getattr(page, "image_%s" % size_name)
        if field_file:
            field_file.delete(save=False)
        field_file.save("page.png", ContentFile(image.make_blob("png")), save=False)


def make_page_annotation(annotation):
    transform_func = None
    if annotation.highlight:
        highlights = json.loads(annotation.highlight)
        if highlights:
            transform_func = draw_highlights(highlights)

    image_bytes = crop_image(
        annotation.page.image.path,
        annotation.left,
        annotation.top,
        annotation.width,
        annotation.height,
        transform_func=transform_func,
    )
    annotation.image.save("page_annotation.png", ContentFile(image_bytes), save=False)


def fix_file_paths(doc):
    pages = Page.objects.filter(document=doc)
    for page in pages:
        fix_file_paths_for_page(page)


def fix_file_paths_for_page(page):
    changed = False
    for size_name, _ in (("original", -1),) + Page.SIZES:
        if size_name == "original":
            field_file = page.image
        else:
            field_file = getattr(page, "image_%s" % size_name)
        real_filename = get_page_filename(page, "page.png", size=size_name)
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
    filename = get_page_annotation_filename(annotation, "annotation.png")
    if annotation.image and filename != annotation.image.name:
        annotation.image.name = filename
        annotation.save()


class DocumentStorer:
    ZIP_BLOCK_LIST = set(["__MACOSX"])

    def __init__(self, user, public=False, collection=None, tags=None):
        self.user = user
        self.public = public
        self.collection = collection
        self.tags = tags

    def __str__(self):
        return "<DocumentStorer for {} in {} public={} tags={}".format(
            self.user, self.collection, self.public, self.tags
        )

    def create_from_file(self, file_obj, filename, directory=None):
        title = filename

        doc = Document.objects.create(
            title=title, user=self.user, public=self.public, pending=True
        )

        if file_obj:
            doc.pdf_file.save(filename, file_obj, save=True)
            process_document_task.delay(doc.pk)

        if self.tags:
            doc.tags.set(*self.tags)
        if self.collection:
            CollectionDocument.objects.get_or_create(
                collection=self.collection, document=doc, directory=directory
            )
        return doc

    def unpack_upload_zip(self, upload):
        return self.unpack_zip(upload.get_file())

    def unpack_zip(self, file_obj):
        if not zipfile.is_zipfile(file_obj):
            return

        with zipfile.ZipFile(file_obj, "r") as zf:
            zip_paths = []
            # step on collect files
            for filepath in zf.namelist():
                path = PurePath(filepath)
                parts = path.parts
                if parts[0] in self.ZIP_BLOCK_LIST:
                    continue
                if path.suffix == ".pdf":
                    zip_paths.append(path)
                # TODO: recursive zip unpacking?
            if not zip_paths:
                return

            doc_paths = remove_common_root_path(zip_paths)
            directories = {}
            for doc_path, zip_path in zip(doc_paths, zip_paths):
                self.ensure_directory_exists(doc_path, directories)
                directory = directories.get(doc_path.parent)
                file_obj = BytesIO(zf.read(str(zip_path)))
                self.create_from_file(file_obj, doc_path.name, directory=directory)

    def ensure_directory_exists(self, path, directories):
        for parent_path in reversed(path.parents):
            if str(parent_path) == ".":
                continue
            if parent_path not in directories:
                parent_parent_path = parent_path.parent
                parent_parent_dir = directories.get(parent_parent_path)
                directory = CollectionDirectory.objects.create(
                    name=str(parent_path),
                    user=self.user,
                    collection=self.collection,
                    parent=parent_parent_dir,
                )
                directories[parent_path] = directory


def remove_common_root_path(paths):
    assert len(paths) > 1
    while True:
        common_root = None
        for path in paths:
            if len(path.parts) == 1:
                return paths
            if common_root is None:
                common_root = path.parts[0]
                continue
            if common_root != path.parts[0]:
                return paths
        paths = [PurePath(os.path.join(*p.parts[1:])) for p in paths]
    return paths


def detect_tables_on_doc(doc, save=True):
    if not doc.get_file_path():
        return
    logger.info("Detecting tables for %s", doc.id)
    with doc.get_local_file() as local_file_path:
        tables = detect_tables(local_file_path)
    doc.properties["_tables"] = tables
    if save:
        doc.save()


def convert_images_to_webp(doc):
    logger.info("Converting page images to webp for Doc %s", doc.id)

    for page in doc.pages.all():
        convert_page_to_webp(page)

    logger.info("Done converting page images to webp for Doc %s", doc.id)


def convert_page_to_webp(page):
    webp_config = get_webp_default_config()

    if page.image:
        pil_image = PILImage.open(page.image).convert("RGB")
        buf = encode_to_webp(pil_image, config=webp_config)
        page.image.storage.save("{}.webp".format(page.image.name), ContentFile(buf))

    for size_name, _ in Page.SIZES:
        field_file = getattr(page, "image_%s" % size_name)
        if not field_file:
            continue
        pil_image = PILImage.open(field_file).convert("RGB")
        buf = encode_to_webp(pil_image, config=webp_config)
        field_file.storage.save("{}.webp".format(field_file.name), ContentFile(buf))


def get_webp_default_config():
    if webp is None:
        raise RuntimeError("The 'webp' python package is not installed")
    return webp.WebPConfig.new(preset=webp.WebPPreset.TEXT, quality=80)


def encode_to_webp(pil_image, config=None):
    if webp is None:
        raise RuntimeError("The 'webp' python package is not installed")
    if config is None:
        config = get_webp_default_config()
    pic = webp.WebPPicture.from_pil(pil_image)
    return pic.encode(config).buffer()
