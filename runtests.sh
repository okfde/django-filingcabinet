#!/bin/sh

export PYTHONPATH=./test_project
export DJANGO_SETTINGS_MODULE=test_project.settings

django-admin test
