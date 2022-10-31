from django.urls import reverse

import pytest

from filingcabinet import views


@pytest.mark.django_db
def test_document_detail(processed_document, client):
    response = client.get(processed_document.get_absolute_url())
    assert response.status_code == 200
    assert processed_document.title in response.content.decode("utf-8")
    assert processed_document.description in response.content.decode("utf-8")


@pytest.mark.django_db
def test_document_list(processed_document, client):
    response = client.get(reverse("filingcabinet:document-list"))
    assert response.status_code == 200
    assert processed_document.title in response.content.decode("utf-8")


@pytest.mark.django_db
def test_document_detail_private(processed_document, client, dummy_user):
    processed_document.public = False
    processed_document.user = dummy_user
    processed_document.save()
    response = client.get(processed_document.get_absolute_url())
    assert response.status_code == 404

    client.force_login(dummy_user)
    response = client.get(processed_document.get_absolute_url())
    assert response.status_code == 200


@pytest.mark.django_db
def test_document_detail_pending(processed_document, client, dummy_user):
    processed_document.pending = True
    processed_document.user = dummy_user
    processed_document.save()
    response = client.get(processed_document.get_absolute_url())
    assert response.status_code == 200
    # iframe with PDF embed present
    assert '<iframe src="{}"'.format(
        processed_document.get_file_url()
    ) in response.content.decode("utf-8")


@pytest.mark.django_db
@pytest.mark.parametrize("initial_slug_val", ["", None])
def test_document_detail_slug_behavior(
    processed_document, client, dummy_user, initial_slug_val
):
    if initial_slug_val is not None:
        processed_document.slug = initial_slug_val
    processed_document.user = dummy_user
    processed_document.save()

    bad_slug_url = reverse(
        "filingcabinet:document-detail",
        kwargs={"pk": processed_document.pk, "slug": "bad"},
    )
    response = client.get(bad_slug_url)
    assert response.status_code == 302
    assert response.headers["Location"] == processed_document.get_absolute_url()

    query_param = "?foo=bar"
    bad_slug_url = bad_slug_url + query_param
    response = client.get(bad_slug_url)
    assert response.status_code == 302
    assert (
        response.headers["Location"]
        == processed_document.get_absolute_url() + query_param
    )

    processed_document.public = False
    processed_document.user = dummy_user
    processed_document.save()
    response = client.get(bad_slug_url)
    assert response.status_code == 404

    client.force_login(dummy_user)
    response = client.get(bad_slug_url)
    assert response.status_code == 302
    assert (
        response.headers["Location"]
        == processed_document.get_absolute_url() + query_param
    )


@pytest.mark.django_db
def test_document_detail_page_query(processed_document, client, monkeypatch):
    monkeypatch.setattr(views, "PREVIEW_PAGE_COUNT", 2)
    response = client.get(processed_document.get_absolute_url() + "?page=1000")
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert '<a href="#page-1"' in content
    assert '<a href="#page-2"' in content
    assert '<a href="#page-3"' not in content
    assert '<a href="#page-4"' not in content

    response = client.get(processed_document.get_absolute_url() + "?page=1")
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert '<a href="#page-1"' in content
    assert '<a href="#page-2"' in content
    assert '<a href="#page-3"' not in content
    assert '<a href="#page-4"' not in content

    response = client.get(processed_document.get_absolute_url() + "?page=2")
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert '<a href="#page-1"' not in content
    assert '<a href="#page-2"' in content
    assert '<a href="#page-3"' in content
    assert '<a href="#page-4"' not in content


@pytest.mark.django_db
def test_document_embed(processed_document, client):
    response = client.get(processed_document.get_absolute_domain_embed_url())
    assert response.status_code == 200
    assert "<h2>{}</h2>".format(
        processed_document.title
    ) not in response.content.decode("utf-8")

    processed_document.slug = ""
    processed_document.save()
    response = client.get(processed_document.get_absolute_domain_embed_url())
    assert response.status_code == 200
    assert "<h2>{}</h2>".format(
        processed_document.title
    ) not in response.content.decode("utf-8")


@pytest.mark.django_db
def test_document_file_detail(processed_document, client, dummy_user):
    processed_document.user = dummy_user
    processed_document.public = False
    processed_document.save()

    response = client.get(processed_document.get_file_url())
    assert response.status_code == 404

    client.force_login(dummy_user)
    response = client.get(processed_document.get_file_url().replace("/ef/", "/aa/"))
    assert response.status_code == 404
    response = client.get(processed_document.get_file_url())
    assert response.status_code == 200
    assert response.headers["Content-Type"] == ""
    assert response.headers["X-Accel-Redirect"].endswith(
        processed_document.get_file_name()
    )
