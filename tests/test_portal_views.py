from django.urls import reverse

import pytest


@pytest.mark.django_db
def test_portal_detail(document_portal, client):
    response = client.get(document_portal.get_absolute_url())
    assert response.status_code == 200
    assert document_portal.title in response.content.decode("utf-8")
    assert document_portal.description in response.content.decode("utf-8")


@pytest.mark.django_db
def test_portal_detail_private(document_portal, client, dummy_user):
    document_portal.public = False
    document_portal.save()
    response = client.get(document_portal.get_absolute_url())
    assert response.status_code == 404

    client.force_login(dummy_user)
    response = client.get(document_portal.get_absolute_url())
    assert response.status_code == 404

    dummy_user.is_superuser = True
    dummy_user.save()
    response = client.get(document_portal.get_absolute_url())
    assert response.status_code == 200


@pytest.mark.django_db
def test_portal_detail_slug_behavior(client):
    bad_slug_url = reverse(
        "filingcabinet:document-portal",
        kwargs={"slug": "bad"},
    )
    response = client.get(bad_slug_url)
    assert response.status_code == 404
