from django.urls import reverse

import pytest

from filingcabinet import get_document_model, get_documentcollection_model

from .factories import DocumentCollectionFactory, DocumentFactory

Document = get_document_model()
DocumentCollection = get_documentcollection_model()


@pytest.mark.django_db
def test_unlisted_document_needs_slug(client, dummy_user):
    doc = DocumentFactory.create(user=dummy_user, public=True, listed=False)

    url = reverse(
        "filingcabinet:document-detail_short",
        kwargs={
            "pk": doc.pk,
        },
    )
    response = client.get(url)
    assert response.status_code == 404

    url = reverse(
        "filingcabinet:document-detail", kwargs={"pk": doc.pk, "slug": doc.slug}
    )
    response = client.get(url)
    assert response.status_code == 200

    client.force_login(dummy_user)
    url = reverse(
        "filingcabinet:document-detail_short",
        kwargs={
            "pk": doc.pk,
        },
    )
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_list_unlisted_document_api(client, dummy_user):
    DocumentFactory.create(user=dummy_user, public=True, listed=False)
    url = reverse("api:document-list")
    response = client.get(url)
    assert len(response.json()["objects"]) == 0
    client.force_login(dummy_user)
    response = client.get(url)
    assert len(response.json()["objects"]) == 1


@pytest.mark.django_db
def test_retrieve_unlisted_document_api(client, dummy_user):
    doc = DocumentFactory.create(user=dummy_user, public=True, listed=False)
    url = reverse("api:document-detail", kwargs={"pk": doc.pk})
    response = client.get(url)
    assert response.status_code == 403

    url = reverse("api:document-detail", kwargs={"pk": doc.pk})
    response = client.get(url + "?uid=" + str(doc.uid))
    assert response.status_code == 200

    client.force_login(dummy_user)
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_unlisted_documentcollection_needs_slug(client, dummy_user):
    collection = DocumentCollectionFactory.create(
        user=dummy_user, public=True, listed=False
    )

    url = reverse(
        "filingcabinet:document-collection_short",
        kwargs={
            "pk": collection.pk,
        },
    )
    response = client.get(url)
    assert response.status_code == 404

    url = reverse(
        "filingcabinet:document-collection",
        kwargs={"pk": collection.pk, "slug": collection.slug},
    )
    response = client.get(url)
    assert response.status_code == 200

    client.force_login(dummy_user)
    url = reverse(
        "filingcabinet:document-collection_short",
        kwargs={
            "pk": collection.pk,
        },
    )
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_list_unlisted_documentcollection_api(client, dummy_user):
    DocumentCollectionFactory.create(user=dummy_user, public=True, listed=False)
    url = reverse("api:documentcollection-list")
    response = client.get(url)
    assert len(response.json()["objects"]) == 0
    client.force_login(dummy_user)
    response = client.get(url)
    assert len(response.json()["objects"]) == 1


@pytest.mark.django_db
def test_retrieve_unlisted_documentcollection_api(client, dummy_user):
    collection = DocumentCollectionFactory.create(
        user=dummy_user, public=True, listed=False
    )
    url = reverse("api:documentcollection-detail", kwargs={"pk": collection.pk})
    response = client.get(url)
    assert response.status_code == 403

    response = client.get(url + "?uid=" + str(collection.uid))
    assert response.status_code == 200

    client.force_login(dummy_user)
    response = client.get(url)
    assert response.status_code == 200
