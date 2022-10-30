from datetime import datetime, timedelta, timezone

import pytest

from filingcabinet.models import CollectionDocument


@pytest.mark.django_db
def test_page_api(client, processed_document):
    # Require document/collection query parameter
    response = client.get("/api/page/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["objects"]) == 0

    response = client.get("/api/page/?document={}".format(processed_document.pk))
    assert response.status_code == 200
    data = response.json()
    assert len(data["objects"]) == 4


@pytest.mark.django_db
def test_page_api_filter_q(client, processed_document):
    page = processed_document.pages.all()[0]
    page.content = "test search test"
    page.save()
    response = client.get(
        "/api/page/?document={}&q=search".format(processed_document.pk)
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["objects"]) == 1
    assert data["objects"][0]["number"] == page.number


@pytest.mark.django_db
def test_page_api_filter_number(client, processed_document):
    response = client.get(
        "/api/page/?document={}&number=3".format(processed_document.pk)
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["objects"]) == 1
    assert data["objects"][0]["number"] == 3


@pytest.mark.django_db
def test_page_api_filter_collection_directory(
    client,
    processed_document,
    document_collection_factory,
    collection_directory_factory,
    dummy_user,
):
    collection = document_collection_factory.create(user=dummy_user)
    collection_dir = collection_directory_factory.create(
        collection=collection, user=dummy_user
    )

    # Put document in collection and directory
    col_doc = CollectionDocument.objects.create(
        collection=collection,
        document=processed_document,
        # directory=collection_dir,
    )

    response = client.get("/api/page/?collection={}".format(collection.pk))
    assert response.status_code == 200
    data = response.json()
    assert len(data["objects"]) == processed_document.num_pages

    response = client.get("/api/page/?collection={}&directory=-".format(collection.pk))
    assert response.status_code == 200
    data = response.json()
    assert len(data["objects"]) == processed_document.num_pages

    response = client.get(
        "/api/page/?collection={}&directory={}".format(collection.pk, collection_dir.pk)
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["objects"]) == 0

    col_doc.directory = collection_dir
    col_doc.save()

    response = client.get("/api/page/?collection={}&directory=-".format(collection.pk))
    assert response.status_code == 200
    data = response.json()
    assert len(data["objects"]) == 0

    response = client.get(
        "/api/page/?collection={}&directory={}".format(collection.pk, collection_dir.pk)
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["objects"]) == processed_document.num_pages

    collection.public = False
    collection.save()

    response = client.get("/api/page/?collection={}".format(collection.pk))
    data = response.json()
    assert len(data["objects"]) == 0

    response = client.get(
        "/api/page/?collection={}&directory={}".format(collection.pk, collection_dir.pk)
    )
    data = response.json()
    assert len(data["objects"]) == 0

    # Login as user
    client.force_login(dummy_user)

    response = client.get("/api/page/?collection={}".format(collection.pk))
    data = response.json()
    assert len(data["objects"]) == processed_document.num_pages

    response = client.get(
        "/api/page/?collection={}&directory={}".format(collection.pk, collection_dir.pk)
    )

    data = response.json()
    assert len(data["objects"]) == processed_document.num_pages


@pytest.mark.django_db
def test_document_api_filter_document(client, processed_document, dummy_user):

    processed_document.public = False
    processed_document.user = dummy_user
    processed_document.save()

    response = client.get("/api/page/?document={}".format(processed_document.pk))
    data = response.json()
    assert len(data["objects"]) == 0

    client.force_login(dummy_user)

    # Filter is ignored on bad input
    response = client.get("/api/page/?document={}".format(processed_document.pk))
    data = response.json()
    assert len(data["objects"]) == processed_document.num_pages


@pytest.mark.django_db
def test_document_api_filter_portal(
    client,
    processed_document,
    document_factory,
    document_portal_factory,
    document_collection_factory,
    page_factory,
    dummy_user,
):

    portal = document_portal_factory.create(public=False)
    processed_document.portal = portal
    processed_document.save()
    document = document_factory(public=True, num_pages=1)
    page_factory(document=document)
    processed_document.tags.add("tag1")
    collection = document_collection_factory.create(user=dummy_user)
    collection.documents.add(processed_document, document)

    response = client.get(
        "/api/page/?collection={}&portal={}".format(collection.pk, portal.pk)
    )
    assert response.status_code == 400

    portal.public = True
    portal.save()

    response = client.get(
        "/api/page/?collection={}&portal={}".format(collection.pk, portal.pk)
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data["objects"]) == processed_document.num_pages


@pytest.mark.django_db
def test_document_api_filter_data_filters(
    client,
    processed_document,
    document_factory,
    page_factory,
    document_collection_factory,
    dummy_user,
):

    publisher_value = "wd1"
    document = document_factory(
        public=True, num_pages=1, data={"publisher": publisher_value, "index": 23}
    )
    page_factory(document=document)
    other_doc = document_factory(public=True)
    page_factory(document=other_doc)
    collection = document_collection_factory.create(
        user=dummy_user,
        settings={
            "filters": [
                {
                    "id": "publisher",
                    "key": "data.publisher",
                    "type": "choice",
                    "facet": False,
                    "label": {"en": "publisher"},
                    "choices": [
                        {"label": {"en": "Some Label"}, "value": publisher_value},
                    ],
                },
                {
                    "id": "index",
                    "key": "data.index",
                    "type": "choice",
                    "datatype": "int",
                    "label": {"en": "index"},
                    "choices": [],
                },
                {
                    "id": "date",
                    "key": "created_at",
                    "type": "daterange",
                    "label": {"en": "date"},
                },
            ]
        },
    )
    collection.documents.add(processed_document, document)

    processed_document.data["publisher"] = "wd1"
    processed_document.data["index"] = 42
    processed_document.save()

    response = client.get(
        "/api/page/?collection={}&data.publisher=".format(collection.pk)
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data["objects"]) == 5

    response = client.get(
        "/api/page/?collection={}&data.publisher={}".format(
            collection.pk, publisher_value
        )
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data["objects"]) == processed_document.num_pages + document.num_pages

    response = client.get(
        "/api/page/?collection={}&data.publisher={}&data.index={}".format(
            collection.pk, publisher_value, "a"
        )
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data["objects"]) == processed_document.num_pages + document.num_pages

    response = client.get(
        "/api/page/?collection={}&data.publisher={}&data.index={}".format(
            collection.pk, publisher_value, 42
        )
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data["objects"]) == processed_document.num_pages


@pytest.mark.django_db
def test_page_api_filter_tags(
    client,
    processed_document,
    document_factory,
    document_collection_factory,
    page_factory,
    dummy_user,
):

    document = document_factory(public=True)
    page_factory(document=document)
    processed_document.tags.add("tag1")
    collection = document_collection_factory.create(user=dummy_user)
    collection.documents.add(processed_document, document)

    response = client.get("/api/page/?collection={}&tag=tag1".format(collection.pk))
    data = response.json()
    assert len(data["objects"]) == processed_document.num_pages


@pytest.mark.django_db
def test_page_api_filter_created_at(
    client,
    processed_document,
    document_factory,
    document_collection_factory,
    page_factory,
    dummy_user,
):

    week = timedelta(days=7)
    date = datetime(2019, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    document = document_factory(public=True, created_at=date, num_pages=1)
    page_factory(document=document)
    processed_document.tags.add("tag1")
    collection = document_collection_factory.create(user=dummy_user)
    collection.documents.add(processed_document, document)

    processed_document.published_at = None
    processed_document.created_at = date + week
    processed_document.save()
    query_date_after = (date + timedelta(days=3)).date().isoformat()

    response = client.get(
        "/api/page/?collection={}&created_at_after={}".format(
            collection.pk, query_date_after
        )
    )
    data = response.json()
    assert len(data["objects"]) == processed_document.num_pages

    response = client.get(
        "/api/page/?collection={}&created_at_before={}".format(
            collection.pk, query_date_after
        )
    )
    data = response.json()
    assert len(data["objects"]) == document.num_pages

    processed_document.created_at = date
    processed_document.published_at = date + week
    processed_document.save()

    response = client.get(
        "/api/page/?collection={}&created_at_after={}".format(
            collection.pk, query_date_after
        )
    )
    data = response.json()
    assert len(data["objects"]) == processed_document.num_pages

    response = client.get(
        "/api/page/?collection={}&created_at_before={}".format(
            collection.pk, query_date_after
        )
    )
    data = response.json()
    assert len(data["objects"]) == document.num_pages

    processed_document.published_at = date
    processed_document.save()

    response = client.get(
        "/api/page/?collection={}&created_at_before={}".format(
            collection.pk, query_date_after
        )
    )
    data = response.json()
    assert len(data["objects"]) == processed_document.num_pages + document.num_pages
