#!/usr/bin/env python

from __future__ import print_function

import os
import re
import codecs

from setuptools import setup, find_packages


def read(*parts):
    filename = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(filename, encoding='utf-8') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="django-filingcabinet",
    version=find_version("filingcabinet", "__init__.py"),
    url='https://github.com/okfde/django-filingcabinet',
    license='MIT',
    description="",
    long_description=read('README.md'),
    author='Stefan Wehrmeyer',
    author_email='mail@stefanwehrmeyer.com',
    packages=find_packages(exclude=("tests", "test_project")),
    install_requires=[
        'Django',
        'wand',
        'pypdf2',
        'pikepdf',
        'Pillow',
        'django-filter',
        'django-taggit',
        'django-mptt',
        'djangorestframework'
    ],
    test_requires=[
        'factory_boy'
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Utilities',
    ]
)
