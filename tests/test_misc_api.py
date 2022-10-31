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
