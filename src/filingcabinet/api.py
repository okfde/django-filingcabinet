from django.conf import settings
from django.core.files.base import File
from django.template.defaultfilters import slugify

from . import get_document_model, get_documentcollection_model
from .models import CollectionDocument
from .pdf_utils import calculcate_content_hash_from_file

Document = get_document_model()
DocumentCollection = get_documentcollection_model()


def create_document(pdf_file_obj, metadata, process=True, update=False):
    content_hash = metadata.get("content_hash")
    if content_hash is None:
        content_hash = calculcate_content_hash_from_file(pdf_file_obj)

    if not metadata.get("slug"):
        metadata["slug"] = slugify(metadata["title"][:250])[:250]

    defaults = {
        "title": metadata["title"],
        "slug": metadata["slug"],
        "description": metadata.get("description", ""),
        "published_at": metadata.get("published_at"),
        "language": metadata.get("language", settings.LANGUAGE_CODE),
        "public": metadata.get("public", True),
        "pending": metadata.get("pending", True),
        "listed": metadata.get("listed", True),
        "allow_annotation": metadata.get("allow_annotation", False),
        "properties": metadata.get("properties", {}),
        "data": metadata.get("data", {}),
        "outline": metadata.get("outline", ""),
        "portal": metadata.get("portal"),
    }

    lookup = {}
    if metadata.get("portal"):
        lookup["portal"] = metadata["portal"]
        foreign_id = metadata.get("properties", {}).get("foreign_id")
        if foreign_id:
            lookup["properties__foreign_id"] = foreign_id
        defaults["content_hash"] = content_hash
    else:
        lookup["content_hash"] = content_hash

    needs_saving = False
    if update:
        needs_saving = True
        doc, _updated = Document.objects.update_or_create(
            **lookup,
            defaults=defaults,
        )
    else:
        doc, needs_saving = Document.objects.get_or_create(**lookup, defaults=defaults)

    if metadata.get("tags"):
        doc.tags.add(*metadata["tags"])

    if metadata["collection"] is not None:
        CollectionDocument.objects.get_or_create(
            collection=metadata["collection"],
            document=doc,
        )

    if not metadata.get("filename"):
        if pdf_file_obj.name:
            metadata["filename"] = pdf_file_obj.name
        else:
            metadata["filename"] = doc.slug + ".pdf"

    if needs_saving and (update or not doc.pdf_file):
        doc.pdf_file.save(metadata["filename"], File(pdf_file_obj), save=True)
        if process:
            doc.process_document(reprocess=update)

    return doc
