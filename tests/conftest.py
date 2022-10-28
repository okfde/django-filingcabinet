import os

import pytest
from pytest_factoryboy import register

from .factories import (
    DocumentCollectionFactory,
    DocumentFactory,
    PageFactory,
    UserFactory,
)

register(UserFactory)
register(DocumentFactory)
register(DocumentCollectionFactory)
register(PageFactory)

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
def processed_document():
    path = "docs/ef/39/5b/ef395b666014488aa551e431e653a1d9"
    doc = DocumentFactory(
        uid="ef395b66-6014-488a-a551-e431e653a1d9",
        pdf_file=f"{path}/example.pdf",
        file_size=260082,
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
