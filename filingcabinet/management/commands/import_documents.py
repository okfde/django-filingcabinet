from datetime import datetime
import glob
import json
import os

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import File
from django.template.defaultfilters import slugify
from django.utils import timezone

from ... import get_document_model
from ...models import DocumentPortal
from ...tasks import process_document_task

Document = get_document_model()


class Command(BaseCommand):
    help = "Load directory of PDFs with meta data JSON files"

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str)

    def handle(self, *args, **options):
        directory = options['directory']
        self.portals = {}
        pdf_files = glob.glob(os.path.join(directory, '*.pdf'))
        for pdf_file in pdf_files:
            print('Importing', pdf_file)
            self.import_pdf(pdf_file)

    def import_pdf(self, pdf_filename):
        metadata_filename = pdf_filename.replace('.pdf', '.json')
        with open(metadata_filename) as f:
            metadata = json.load(f)

        published_at = None
        if metadata.get('published_at'):
            published_at = datetime.fromisoformat(metadata['published_at'])
            tz = timezone.get_default_timezone()
            if published_at.tzinfo is not None:
                published_at = tz.normalize(published_at)
            else:
                published_at = tz.localize(published_at)

        portal = None
        if metadata.get('portal'):
            portal = self.get_portal(metadata['portal'])

        doc, created = Document.objects.get_or_create(
            content_hash=metadata['content_hash'],
            defaults={
                'title': metadata['title'],
                'slug': slugify(metadata['title'][:250])[:250],
                'description': metadata.get('description', ''),
                'published_at': published_at,
                'language': metadata.get('language', settings.LANGUAGE_CODE),
                'public': True,
                'pending': True,
                'allow_annotation': metadata.get('allow_annotation', False),
                'properties': metadata.get('properties', {}),
                'data': metadata.get('data', {}),
                'portal': portal
            }
        )
        if created and not doc.pdf_file:
            with open(pdf_filename, 'rb') as file_obj:
                doc.pdf_file.save(
                    os.path.basename(pdf_filename),
                    File(file_obj),
                    save=True
                )
            process_document_task.delay(doc.pk)

    def get_portal(self, portal_slug):
        if portal_slug not in self.portals:
            self.portals[portal_slug] = DocumentPortal.objects.get(
                slug=portal_slug
            )
        return self.portals[portal_slug]
