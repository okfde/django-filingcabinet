from django.urls import reverse

import pytest


@pytest.mark.django_db
def test_collection_detail(document_collection, client):
    response = client.get(document_collection.get_absolute_url())
    assert response.status_code == 200
    assert document_collection.title in response.content.decode("utf-8")
    assert document_collection.description in response.content.decode("utf-8")


@pytest.mark.django_db
def test_collection_detail_private(document_collection, client, dummy_user):
    document_collection.public = False
    document_collection.user = dummy_user
    document_collection.save()
    response = client.get(document_collection.get_absolute_url())
    assert response.status_code == 404

    client.force_login(dummy_user)
    response = client.get(document_collection.get_absolute_url())
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("initial_slug_val", ["", None])
def test_collection_detail_slug_behavior(
    document_collection, client, dummy_user, initial_slug_val
):
    if initial_slug_val is not None:
        document_collection.slug = initial_slug_val
    document_collection.user = dummy_user
    document_collection.save()

    bad_slug_url = reverse(
        "filingcabinet:document-collection",
        kwargs={"pk": document_collection.pk, "slug": "bad"},
    )
    response = client.get(bad_slug_url)
    assert response.status_code == 302
    assert response.headers["Location"] == document_collection.get_absolute_url()

    query_param = "?foo=bar"
    bad_slug_url = bad_slug_url + query_param
    response = client.get(bad_slug_url)
    assert response.status_code == 302
    assert (
        response.headers["Location"]
        == document_collection.get_absolute_url() + query_param
    )

    document_collection.public = False
    document_collection.user = dummy_user
    document_collection.save()
    response = client.get(bad_slug_url)
    assert response.status_code == 404

    client.force_login(dummy_user)
    response = client.get(bad_slug_url)
    assert response.status_code == 302
    assert (
        response.headers["Location"]
        == document_collection.get_absolute_url() + query_param
    )


@pytest.mark.django_db
def test_collection_embed(document_collection, client):
    response = client.get(document_collection.get_absolute_domain_embed_url())
    assert response.status_code == 200
    assert "<h2>{}</h2>".format(
        document_collection.title
    ) not in response.content.decode("utf-8")

    document_collection.slug = ""
    document_collection.save()
    response = client.get(document_collection.get_absolute_domain_embed_url())
    assert response.status_code == 200
    assert "<h2>{}</h2>".format(
        document_collection.title
    ) not in response.content.decode("utf-8")
