import glob
import hashlib
import json
import os
from datetime import datetime

from django.conf import settings
from django.core.files.base import File
from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify
from django.utils import timezone

from ... import get_document_model, get_documentcollection_model
from ...models import CollectionDocument, DocumentPortal
from ...tasks import process_document_task

Document = get_document_model()
DocumentCollection = get_documentcollection_model()


def parse_date(date_str):
    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        return None
    tz = timezone.get_default_timezone()
    if date.tzinfo is not None:
        date = tz.normalize(date)
    else:
        date = tz.localize(date)
    return date


class Command(BaseCommand):
    help = "Load directory of PDFs with meta data JSON files"

    def add_arguments(self, parser):
        parser.add_argument("directory", type=str)

    def handle(self, *args, **options):
        directory = options["directory"]
        self.portals = {}
        self.collections = {}
        pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
        for pdf_file in pdf_files:
            print("Importing", pdf_file)
            self.import_pdf(pdf_file)

    def get_content_hash(self, pdf_filename):
        h = hashlib.sha256()
        with open(pdf_filename, "rb") as f:
            while True:
                chunk = f.read(h.block_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def import_pdf(self, pdf_filename):
        metadata_filename = pdf_filename.replace(".pdf", ".json")
        if os.path.exists(metadata_filename):
            with open(metadata_filename) as f:
                metadata = json.load(f)
        else:
            metadata = {"title": ""}

        content_hash = metadata.get("content_hash")
        if content_hash is None:
            content_hash = self.get_content_hash(pdf_filename)

        published_at = None
        if metadata.get("published_at"):
            published_at = parse_date(metadata["published_at"])

        portal = None
        if metadata.get("portal"):
            portal = self.get_portal(metadata["portal"])

        collection = None
        if metadata.get("collection"):
            collection = self.get_collection(metadata["collection"])

        doc, created = Document.objects.get_or_create(
            content_hash=content_hash,
            defaults={
                "title": metadata["title"],
                "slug": slugify(metadata["title"][:250])[:250],
                "description": metadata.get("description", ""),
                "published_at": published_at,
                "language": metadata.get("language", settings.LANGUAGE_CODE),
                "public": metadata.get("public", True),
                "pending": metadata.get("pending", True),
                "listed": metadata.get("listed", True),
                "allow_annotation": metadata.get("allow_annotation", False),
                "properties": metadata.get("properties", {}),
                "data": metadata.get("data", {}),
                "outline": metadata.get("outline", ""),
                "portal": portal,
            },
        )

        if collection is not None:
            CollectionDocument.objects.create(
                collection=collection,
                document=doc,
            )

        if created and not doc.pdf_file:
            with open(pdf_filename, "rb") as file_obj:
                doc.pdf_file.save(
                    os.path.basename(pdf_filename), File(file_obj), save=True
                )
            process_document_task.delay(doc.pk)

    def get_portal(self, portal_slug):
        if portal_slug not in self.portals:
            self.portals[portal_slug] = DocumentPortal.objects.get(slug=portal_slug)
        return self.portals[portal_slug]

    def get_collection(self, collection_id):
        if collection_id not in self.collections:
            self.collections[collection_id] = DocumentCollection.objects.get(
                id=collection_id
            )
        return self.collections[collection_id]
