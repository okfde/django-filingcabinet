from django.urls import reverse

import pytest

from filingcabinet.models import CollectionDirectory, CollectionDocument

from . import DocumentCollectionFactory, DocumentFactory


@pytest.mark.django_db
def test_documentcollection_pagination(client, dummy_user):
    collection = DocumentCollectionFactory(user=dummy_user)
    for i in range(100):
        directory = CollectionDirectory(
            name=f"Directory {i}",
            user=dummy_user,
            collection=collection,
        )
        CollectionDirectory.add_root(instance=directory)

    for _ in range(100):
        document = DocumentFactory()
        CollectionDocument.objects.create(
            collection=collection,
            document=document,
        )

    url = reverse("api:documentcollection-detail", kwargs={"pk": collection.pk})
    response = client.get(url)
    assert response.status_code == 200
    # Directories are not paginated, because there is no other endpoint to query them
    assert len(response.json()["directories"]) == 100

    # Document are paginated, because we have a seperate endpoint to query them
    assert len(response.json()["documents"]) == 50
