import glob
import hashlib
import json
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from ... import get_document_model, get_documentcollection_model
from ...api import import_document
from ...models import DocumentPortal

Document = get_document_model()
DocumentCollection = get_documentcollection_model()


def parse_date(date_str):
    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        return None
    if timezone.is_naive(date):
        date = date.replace(tzinfo=timezone.get_default_timezone())
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
            self.stdout.write("Importing %s" % pdf_file)
            self.import_pdf(pdf_file)

    def get_content_hash(self, pdf_filename):
        h = hashlib.sha1()
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

        metadata["filename"] = os.path.basename(pdf_filename)

        if metadata.get("published_at"):
            metadata["published_at"] = parse_date(metadata["published_at"])
        else:
            metadata["published_at"] = None

        if metadata.get("portal"):
            metadata["portal"] = self.get_portal(metadata["portal"])
        else:
            metadata["portal"] = None

        if metadata.get("collection"):
            metadata["collection"] = self.get_collection(metadata["collection"])
        else:
            metadata["collection"] = None

        with open(pdf_filename, "rb") as pdf_fileobj:
            import_document(pdf_fileobj, metadata)

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
