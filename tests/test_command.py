import json
from io import StringIO
from pathlib import PosixPath

from django.core.management import call_command

import pytest

from filingcabinet import get_document_model

Document = get_document_model()


@pytest.mark.django_db
def test_import_command(tmp_media_path, processed_document, document_collection):
    directory = PosixPath(processed_document.pdf_file.path).parent
    metadata = {
        "title": "Test title",
        "slug": "test-title",
        "tags": ["tag1", "tag2"],
        "public": True,
        "collection": document_collection.id,
        "published_at": "2020-01-01T00:00:00+00:00",
    }
    json_path = processed_document.pdf_file.path.replace(".pdf", ".json")
    with open(json_path, "w") as f:
        json.dump(metadata, f)

    out = StringIO()
    call_command(
        "import_documents",
        directory,
        stdout=out,
        stderr=StringIO(),
    )
    assert "Importing %s" % processed_document.pdf_file.path in out.getvalue()
    doc = Document.objects.exclude(pk=processed_document.pk).first()
    assert doc is not None
    assert doc.title == metadata["title"]
    assert doc.slug == metadata["slug"]
    assert set(doc.tags.values_list("name", flat=True)) == set(metadata["tags"])
    assert doc.public == metadata["public"]
    assert (
        doc.filingcabinet_collectiondocument.first().collection == document_collection
    )
    assert doc.published_at.isoformat() == metadata["published_at"]

    # second time match with content hash
    call_command(
        "import_documents",
        directory,
        stdout=out,
        stderr=StringIO(),
    )
    assert "Importing %s" % processed_document.pdf_file.path in out.getvalue()
    assert Document.objects.exclude(pk=processed_document.pk).count() == 1
