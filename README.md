# django-filingcabinet

A Django app that manages documents with pages, page annotations and collections. [Optionally can use document feature annotation and prediction.](https://github.com/okfde/fcdocs-annotate)


## Quickstart with Docker

Install [docker](https://docs.docker.com/get-docker/) and [docker compose plugin](https://docs.docker.com/compose/install/).

```bash
docker-compose run --rm web python manage.py migrate
# Create a user account
docker-compose run --rm web python manage.py createsuperuser
# Start all services (nginx, web, worker, broker)
docker-compose up
# Nginx will be available at localhost:8080 by default
```


### Example User flow

Access the admin interface at: http://localhost:8080/admin/

Set the correct site domain at: http://localhost:8080/admin/sites/site/

Upload documents at: http://localhost:8080/admin/filingcabinet/document/


## Integrate into a Django project

See the `fc_project` dir for an example of a Django project that uses `django-filingcabinet` and the feature prediction in `fcdocs-annotate`.

## Management command to import directory of PDFs

```bash
python manage.py import_documents <directory of *.pdf files>
```

You can provide extra metadata as a JSON file with the same name as the PDF file. E.g.:

```json
{
    "title": "",
    "description": "",
    "language": "<ISO language code>",
    "published_at": "<ISO date string>",
    "public": true,
    "listed": true,
    "properties": {
        "custom": "properties"
    },
    "data": {
        "filterable": "data"
    },
    "tags": ["Tag"],
    "collection": 123
}
```

## Manual feature annotation

You can generate training data by annotating documents in your database.
Create features in the admin and then visit:

http://localhost:8080/documents/features/


## Feature prediction on documents

Use a ZIP-export of a kedro feature model: https://github.com/okfde/fcdocs#packaging-the-models

Upload a packaged feature model as .zip: http://localhost:8080/admin/fcdocs_annotation/feature/

Start feature prediction tasks on documents via document admin action dropdown.


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
