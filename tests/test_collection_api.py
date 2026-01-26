from django.urls import reverse

import pytest

from filingcabinet.api_serializers import MAX_COLLECTION_DOCS
from filingcabinet.models import (
    CollectionDirectory,
    CollectionDocument,
)

from . import DocumentCollectionFactory, DocumentFactory


def make_collection_and_documents(dummy_user):
    collections = [
        DocumentCollectionFactory(user=dummy_user),
        DocumentCollectionFactory(user=dummy_user),
    ]
    for collection in collections:
        for i in range(10):
            directory = CollectionDirectory(
                name=f"Directory {i}",
                user=dummy_user,
                collection=collection,
            )
            CollectionDirectory.add_root(instance=directory)

        for _ in range(MAX_COLLECTION_DOCS + 10):
            document = DocumentFactory(public=True)
            CollectionDocument.objects.create(
                collection=collection,
                document=document,
            )

    # interleave documents from different collections
    for collection in collections:
        parent_directory = CollectionDirectory(
            name=f"Directory {i}",
            user=dummy_user,
            collection=collection,
        )
        CollectionDirectory.add_root(instance=parent_directory)
        directory = CollectionDirectory(
            name=f"Sub Directory {i}",
            user=dummy_user,
            collection=collection,
        )
        parent_directory.add_child(instance=directory)
        for _ in range(20):
            document = DocumentFactory(public=True)
            CollectionDocument.objects.create(
                collection=collection,
                directory=directory,
                document=document,
            )
    return collection, directory


@pytest.mark.django_db
def test_documentcollection_api_sql_queries(
    client, dummy_user, django_assert_num_queries
):
    collection, directory = make_collection_and_documents(dummy_user)

    list_url = reverse("api:documentcollection-list")
    with django_assert_num_queries(4):
        # - 1 for the collection count
        # - 1 for the collection list
        # - 1 for the directories
        # - 1 for the documents
        response = client.get(list_url)
    assert response.status_code == 200
    assert len(response.json()["objects"]) == 2

    detail_url = reverse("api:documentcollection-detail", kwargs={"pk": collection.pk})
    with django_assert_num_queries(3):
        # - 1 for the collection
        # - 1 for the directories at root
        # - 1 for the documents at root
        response = client.get(detail_url)
    assert response.status_code == 200

    detail_directory_url = reverse(
        "api:documentcollection-detail", kwargs={"pk": collection.pk}
    ) + "?directory={}".format(directory.id)
    with django_assert_num_queries(5):
        # - 1 for the collection
        # - 1 for the cover image at first document at the root of the collection
        # - 1 for the directories in the directory
        # - 1 for the documents in the  directory
        # - 1 for the directory stack (ancestors)
        response = client.get(detail_directory_url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_documentcollection_counts(client, dummy_user):
    collection, directory = make_collection_and_documents(dummy_user)

    detail_url = reverse("api:documentcollection-detail", kwargs={"pk": collection.pk})
    response = client.get(detail_url)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["document_count"] == MAX_COLLECTION_DOCS + 10 + 20
    assert response_data["document_directory_count"] == MAX_COLLECTION_DOCS + 10
    assert len(response_data["directories"]) == 11
    assert len(response_data["documents"]) == MAX_COLLECTION_DOCS

    detail_directory_url = reverse(
        "api:documentcollection-detail", kwargs={"pk": collection.pk}
    ) + "?directory={}".format(directory.id)
    response = client.get(detail_directory_url)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["document_count"] == MAX_COLLECTION_DOCS + 10 + 20
    assert response_data["document_directory_count"] == 20
    assert len(response_data["directories"]) == 0
    assert len(response_data["documents"]) == 20
    assert len(response_data["directory_stack"]) == 1
