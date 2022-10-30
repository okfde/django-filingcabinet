import pytest


@pytest.mark.django_db
def test_page_api(client, processed_document):
    response = client.get(
        "/api/page/?document={}&format=rss".format(processed_document.pk)
    )
    content = response.content.decode("utf-8")
    for i in range(1, processed_document.num_pages + 1):
        assert (
            "<title>{} (p. {})</title>".format(processed_document.title, i) in content
        )
