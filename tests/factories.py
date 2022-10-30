from django.conf import settings
from django.template.defaultfilters import slugify

import factory

from filingcabinet import get_document_model, get_documentcollection_model
from filingcabinet.models import CollectionDirectory, DocumentPortal, Page

Document = get_document_model()
DocumentCollection = get_documentcollection_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document

    title = factory.Sequence(lambda n: "Document {}".format(n))
    slug = factory.LazyAttribute(lambda o: slugify(o.title))


class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page

    document = factory.SubFactory(DocumentFactory)
    number = factory.Sequence(lambda n: n)


class DocumentCollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DocumentCollection

    title = factory.Sequence(lambda n: "DocumentCollection {}".format(n))
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
    user = factory.SubFactory(UserFactory)


class CollectionDirectoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CollectionDirectory

    collection = factory.SubFactory(DocumentCollectionFactory)
    name = factory.Sequence(lambda n: "CollectionDirectory {}".format(n))
    depth = 0


class DocumentPortalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DocumentPortal

    title = factory.Sequence(lambda n: "DocumentPortal {}".format(n))
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
