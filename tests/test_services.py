import zipfile
from io import BytesIO
from pathlib import PurePath

import pytest

from filingcabinet import services
from filingcabinet.models import CollectionDocument
from filingcabinet.services import (
    DocumentStorer,
    detect_tables_on_doc,
    remove_common_root_path,
)


def test_common_root_detection():
    paths = [
        PurePath("a/b/c/d/test.pdf"),
        PurePath("a/b/c/d/e/test.pdf"),
        PurePath("a/b/c/e/a/test.pdf"),
    ]
    result = remove_common_root_path(paths)
    assert result == [
        PurePath("d/test.pdf"),
        PurePath("d/e/test.pdf"),
        PurePath("e/a/test.pdf"),
    ]


@pytest.mark.django_db
def test_table_detection(processed_document, monkeypatch):
    def detect_tables(path):
        assert (
            PurePath(path).suffix == PurePath(processed_document.pdf_file.path).suffix
        )
        return [1, 2, 3]

    monkeypatch.setattr(services, "detect_tables", detect_tables)
    detect_tables_on_doc(processed_document, save=False)
    assert processed_document.properties["_tables"] == [1, 2, 3]


@pytest.mark.django_db
def test_zip_unpacking(dummy_user, document_collection_factory, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    fh = BytesIO()
    zfh = zipfile.ZipFile(fh, "w")
    zfh.writestr("foo/somefile.txt", "test")
    zfh.writestr("bar/somefile.txt", "test")
    zfh.writestr("foo/bar/1_somefile.pdf", b"pdf")
    zfh.writestr("foo/bar/baz/2_otherfile.pdf", b"pdf")
    zfh.writestr("foo/bar/baz/boo/3_otherfile.pdf", b"pdf")
    zfh.close()
    fh.seek(0)
    collection = document_collection_factory()
    storer = DocumentStorer(
        dummy_user, public=True, collection=collection, tags=["tag1"]
    )
    storer.unpack_zip(fh)

    col_docs = CollectionDocument.objects.filter(collection=collection).order_by(
        "document__title"
    )
    assert len(col_docs) == 3
    assert col_docs[0].document.tags.filter(name="tag1").exists()
    assert col_docs[0].directory is None
    assert col_docs[1].document.tags.filter(name="tag1").exists()
    assert col_docs[1].directory.name == "baz"
    assert col_docs[2].document.tags.filter(name="tag1").exists()
    assert col_docs[2].directory.name == "boo"
    assert col_docs[2].directory.get_parent().name == "baz"


@pytest.mark.django_db
@pytest.mark.slow
def test_processing_document(processed_document):
    page = processed_document.pages.all()[0]
    page.pending = True
    page.save()
    processed_document.pages.filter(pending=False).delete()
    processed_document.num_pages = 0
    processed_document.save()

    processed_document.process_document(reprocess=False)

    page.refresh_from_db()
    assert not page.pending
    processed_document.refresh_from_db()
    assert not processed_document.pending
    assert processed_document.pages.count() == 4
    assert processed_document.num_pages == 4
