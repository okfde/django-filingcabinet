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
# Start all services (web, worker, broker)
docker-compose up
```

Access the admin interface at http://localhost:5000/admin/

### Example User flow

Upload documents at: http://localhost:5000/admin/filingcabinet/document/
