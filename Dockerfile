FROM python:3.10

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE fc_project.settings

RUN apt-get update && apt-get install -y --no-install-recommends imagemagick tesseract-ocr poppler-utils qpdf

WORKDIR /project

RUN useradd -m -r appuser && chown appuser /project

COPY requirements-production.txt .
RUN pip install -r requirements-production.txt

# copy the whole project except what is in .dockerignore
COPY . .

USER appuser
EXPOSE 8000

RUN python ./manage.py collectstatic
