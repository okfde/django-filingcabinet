import os
import shutil
import uuid

import pytest
from pytest_factoryboy import register

from .factories import (
    CollectionDirectoryFactory,
    DocumentCollectionFactory,
    DocumentFactory,
    DocumentPortalFactory,
    PageFactory,
    UserFactory,
)

register(UserFactory)
register(DocumentFactory)
register(DocumentCollectionFactory)
register(PageFactory)
register(CollectionDirectoryFactory)
register(DocumentPortalFactory)

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture
def dummy_user():
    yield UserFactory(username="dummy")


@pytest.fixture()
def page(browser):
    context = browser.new_context(locale="en")
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture()
def long_timeout_page(browser):
    context = browser.new_context(locale="en")
    context.set_default_timeout(10000)
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture()
def processed_document(tmp_path, dummy_user, settings):
    path = "{}/ef/39/5b/ef395b666014488aa551e431e653a1d9".format(
        settings.FILINGCABINET_MEDIA_PUBLIC_PREFIX
    )
    shutil.copytree(
        settings.TEST_DATA_ROOT / "example-doc",
        tmp_path / path,
    )
    settings.MEDIA_ROOT = tmp_path

    doc = DocumentFactory(
        title="Test Document",
        description="Description of Test Document",
        uid=uuid.UUID("ef395b66-6014-488a-a551-e431e653a1d9"),
        pdf_file=f"{path}/example.pdf",
        file_size=260082,
        user=dummy_user,
        pending=False,
        num_pages=4,
        language="de",
        public=True,
    )
    for i in range(1, 5):
        PageFactory(
            document=doc,
            number=i,
            width=2481,
            height=3508,
            image=f"{path}/page-p{i}-original.png",
            image_large=f"{path}/page-p{i}-large.png",
            image_normal=f"{path}/page-p{i}-normal.png",
            image_small=f"{path}/page-p{i}-small.png",
        )
    yield doc


@pytest.fixture()
def document_collection(processed_document, document_collection_factory):
    collection = document_collection_factory(
        title="Test Collection",
        slug="test-collection",
        description="Test Collection Description",
        public=True,
    )
    collection.documents.add(processed_document)
    yield collection


@pytest.fixture()
def document_portal(processed_document, document_portal_factory):
    portal = document_portal_factory(
        title="Test Portal",
        slug="test-portal",
        description="Test Portal Description",
        public=True,
    )
    processed_document.portal = portal
    processed_document.save()

    yield portal
