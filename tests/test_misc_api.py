from urllib.parse import quote

from django.urls import reverse

import pytest


@pytest.mark.django_db
def test_rss_api(client, processed_document):
    response = client.get(
        "/api/page/?document={}&format=rss".format(processed_document.pk)
    )
    content = response.content.decode("utf-8")
    for i in range(1, processed_document.num_pages + 1):
        assert (
            "<title>{} (p. {})</title>".format(processed_document.title, i) in content
        )


@pytest.mark.django_db
def test_oembed_api(client, processed_document, settings):
    settings.SITE_URL = "https://example.com"

    oembed_url = reverse("api:document-oembed") + "?url={}".format(
        quote(processed_document.get_absolute_domain_url())
    )
    response = client.get(oembed_url + "&format=xml")
    # content negotiation fails already for format XML
    assert response.status_code == 404

    response = client.get(oembed_url)
    data = response.json()
    assert data["version"] == "1.0"
    assert data["title"] == processed_document.title
    assert data["html"].startswith("<iframe")
    assert processed_document.get_absolute_domain_embed_url() in data["html"]


@pytest.mark.django_db
def test_oembed_collection_api(client, document_collection, settings):
    settings.SITE_URL = "https://example.com"

    oembed_url = reverse("api:documentcollection-oembed") + "?url={}".format(
        quote(document_collection.get_absolute_domain_url())
    )
    response = client.get(oembed_url + "&format=xml")
    # content negotiation fails already for format XML
    assert response.status_code == 404

    response = client.get(oembed_url)
    data = response.json()
    assert data["version"] == "1.0"
    assert data["title"] == document_collection.title
    assert data["html"].startswith("<iframe")
    assert document_collection.get_absolute_domain_embed_url() in data["html"]


@pytest.mark.django_db
def test_oembed_portal_api(client, document_portal, settings):
    settings.SITE_URL = "https://example.com"

    oembed_url = reverse("api:documentportal-oembed") + "?url={}".format(
        quote(document_portal.get_absolute_domain_url())
    )
    response = client.get(oembed_url + "&format=xml")
    # content negotiation fails already for format XML
    assert response.status_code == 404

    response = client.get(oembed_url)
    data = response.json()
    assert data["version"] == "1.0"
    assert data["title"] == document_portal.title
    assert data["html"].startswith("<iframe")
    assert document_portal.get_absolute_domain_embed_url() in data["html"]


@pytest.mark.django_db
def test_document_portal_api(client, document_portal):
    detail_url = reverse("api:documentportal-detail", kwargs={"pk": document_portal.pk})
    response = client.get(detail_url)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document_portal.pk
    assert data["title"] == document_portal.title
    assert data["document_count"] == 1
    assert data["document_directory_count"] == 1
    assert len(data["documents"]) == 1
    assert len(data["directories"]) == 0
