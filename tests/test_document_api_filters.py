from datetime import datetime, timedelta, timezone

import pytest

from filingcabinet.models import CollectionDocument


@pytest.mark.django_db
def test_document_api(client, document_factory):
    document_factory.create_batch(10, public=True)
    response = client.get("/api/document/")
    assert response.status_code == 200
    assert len(response.json()["objects"]) == 10


@pytest.mark.django_db
def test_document_api_filter_collection_directory(
    client,
    document_factory,
    document_collection_factory,
    collection_directory_factory,
    dummy_user,
):
    collection = document_collection_factory.create(user=dummy_user)
    collection_dir = collection_directory_factory.create(
        collection=collection, user=dummy_user
    )

    document_factory.create_batch(5, public=True, user=dummy_user)

    # Put some documents in collection, first in directory
    documents = document_factory.create_batch(10, public=True, user=dummy_user)
    CollectionDocument.objects.create(
        collection=collection,
        document=documents[0],
        directory=collection_dir,
    )
    collection.documents.add(*documents[1:])

    response = client.get("/api/document/?collection={}".format(collection.pk))
    assert response.status_code == 200
    data = response.json()
    assert len(data["objects"]) == 10

    response = client.get(
        "/api/document/?collection={}&directory=-".format(collection.pk)
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["objects"]) == 9
    assert documents[0].id not in {d["id"] for d in data["objects"]}

    response = client.get(
        "/api/document/?collection={}&directory={}".format(
            collection.pk, collection_dir.pk
        )
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["objects"]) == 1
    assert data["objects"][0]["id"] == documents[0].pk

    collection.public = False
    collection.save()

    response = client.get("/api/document/?collection={}".format(collection.pk))
    data = response.json()
    assert len(data["objects"]) == 0

    response = client.get("/api/document/?directory={}".format(collection_dir.pk))
    data = response.json()
    assert len(data["objects"]) == 0

    # Login as user
    client.force_login(dummy_user)

    response = client.get("/api/document/?collection={}".format(collection.pk))
    data = response.json()
    assert len(data["objects"]) == 10

    response = client.get("/api/document/?directory={}".format(collection_dir.pk))
    data = response.json()
    assert len(data["objects"]) == 1


@pytest.mark.django_db
def test_document_api_filter_id(
    client,
    document_factory,
):
    documents = document_factory.create_batch(5, public=True)

    response = client.get(
        "/api/document/?ids={},{}".format(documents[0].pk, documents[1].pk)
    )
    data = response.json()
    assert len(data["objects"]) == 2
    assert documents[0].id in {d["id"] for d in data["objects"]}
    assert documents[1].id in {d["id"] for d in data["objects"]}

    # Filter is ignored on bad input
    response = client.get(
        "/api/document/?ids={},{},a".format(documents[0].pk, documents[1].pk)
    )
    data = response.json()
    assert len(data["objects"]) == 5


@pytest.mark.django_db
def test_document_api_filter_portal(client, document_factory, document_portal_factory):
    portal = document_portal_factory.create(public=False)
    document_factory.create_batch(5, public=True, portal=portal)

    response = client.get("/api/document/?portal={}".format(portal.pk))
    assert response.status_code == 400

    portal.public = True
    portal.save()

    response = client.get("/api/document/?portal={}".format(portal.pk))
    data = response.json()
    assert response.status_code == 200
    assert len(data["objects"]) == 5


@pytest.mark.django_db
def test_document_api_filter_data_filters(
    client, document_factory, document_portal_factory
):
    publisher_value = "wd1"
    portal = document_portal_factory.create(
        public=True,
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
    documents = document_factory.create_batch(5, public=True, portal=portal)
    documents[0].data["publisher"] = "wd1"
    documents[0].data["index"] = 42
    documents[0].save()

    documents[1].data["publisher"] = "wd1"
    documents[1].data["index"] = 23
    documents[1].save()

    response = client.get("/api/document/?portal={}&data.publisher=".format(portal.pk))
    data = response.json()
    assert response.status_code == 200
    assert len(data["objects"]) == 5

    response = client.get(
        "/api/document/?portal={}&data.publisher={}".format(portal.pk, publisher_value)
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data["objects"]) == 2
    assert data["objects"][0]["id"] == documents[0].pk

    response = client.get(
        "/api/document/?portal={}&data.publisher={}&data.index={}".format(
            portal.pk, publisher_value, "a"
        )
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data["objects"]) == 2
    assert data["objects"][0]["id"] == documents[0].pk

    response = client.get(
        "/api/document/?portal={}&data.publisher={}&data.index={}".format(
            portal.pk, publisher_value, 42
        )
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data["objects"]) == 1
    assert data["objects"][0]["id"] == documents[0].pk


@pytest.mark.django_db
def test_document_api_filter_tags(
    client,
    document_factory,
):
    documents = document_factory.create_batch(5, public=True)
    documents[0].tags.add("tag1")

    response = client.get("/api/document/?tag=tag1")
    data = response.json()
    assert len(data["objects"]) == 1
    assert documents[0].id in {d["id"] for d in data["objects"]}


@pytest.mark.django_db
def test_document_api_filter_created_at(
    client,
    document_factory,
):
    week = timedelta(days=7)
    date = datetime(2019, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    documents = document_factory.create_batch(5, public=True, created_at=date)
    documents[0].created_at = date + week
    documents[0].save()
    documents[1].published_at = date + week
    documents[1].save()

    query_date_after = (date + timedelta(days=3)).date().isoformat()

    response = client.get("/api/document/?created_at_after={}".format(query_date_after))
    data = response.json()
    assert len(data["objects"]) == 2
    ids = {d["id"] for d in data["objects"]}
    assert documents[0].id in ids
    assert documents[1].id in ids

    response = client.get(
        "/api/document/?created_at_before={}".format(query_date_after)
    )
    data = response.json()
    assert len(data["objects"]) == 3
    ids = {d["id"] for d in data["objects"]}
    assert {documents[2].id, documents[3].id, documents[4].id} == ids
