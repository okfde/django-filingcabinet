FROM node:16-alpine as jsbuilder
WORKDIR /usr/src/js
COPY package.json yarn.lock /usr/src/js/
RUN yarn install
COPY frontend /usr/src/js/frontend
COPY vite.config.js .
RUN yarn build

# ---

FROM python:3.10

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE fc_project.settings

RUN apt-get update && apt-get install -y --no-install-recommends imagemagick tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu tesseract-ocr-nld tesseract-ocr-osd poppler-utils qpdf

WORKDIR /project

RUN useradd -m -r appuser && chown appuser /project

COPY requirements-production.txt .
RUN pip install -r requirements-production.txt

# copy the whole project except what is in .dockerignore
COPY src .
COPY manage.py .
COPY --from=jsbuilder /usr/src/js/build /project/build

USER appuser
EXPOSE 8000

RUN python ./manage.py collectstatic
