# django-filingcabinet

A Django app that manages documents with pages, annotations and collections.

# @okfde/filingcabinet

Includes `@okfde/filingcabinet` JS package with Vue components.


## Quickstart with Docker

Install [docker](https://docs.docker.com/get-docker/) and [docker compose plugin](https://docs.docker.com/compose/install/).

```bash
docker-compose run --rm web python manage.py migrate
# Create a user account
docker-compose run --rm web python manage.py createsuperuser
# Start all services (nginx, web, worker, broker)
docker-compose up
```


### Example User flow

Access the admin interface at: http://localhost:8080/admin/

Set the correct site domain at: http://localhost:8080/admin/sites/site/

Upload feature model at: http://localhost:8080/admin/fcdocs_annotation/feature/

Upload documents at: http://localhost:8080/admin/filingcabinet/document/

Predict document feature on document via document admin action dropdown.


## Prediction microservice

You can use the prediction API stand-alone as a microservice. Send JSON with a document URL and a callback URL to a feature prediction API endpoint:

```bash
curl --request POST \
  --url http://localhost:8080/api/feature/1/predict/ \
  --header 'Content-Type: application/json' \
  --data '{"document_url": "http://example.com/document.pdf",
           "callback_url": "http://example.com/callback/"}'
```

This will return a JSON document like this:

```json
{
        "callback_url": "http://example.com/callback/", 
        "document_url": "http://example.com/document.pdf",
        "feature_id": 1,
        "task_id": "93e84b09-78ca-4c27-97ce-90b23d13fae5",
        "result": null,
        "status": "pending",
        "details": ""
}
```


The callback URL will be POSTed a JSON document like this:

```json
{
        "callback_url": "http://example.com/callback/", 
        "document_url": "http://example.com/document.pdf",
        "feature_id": 1,
        "task_id": "93e84b09-78ca-4c27-97ce-90b23d13fae5",
        "result": false,
        "status": "complete",
        "details": ""
}
```
