from django.conf import settings
from django.template.defaultfilters import slugify

import factory

from filingcabinet import get_document_model, get_documentcollection_model
from filingcabinet.models import CollectionDirectory

Document = get_document_model()
DocumentCollection = get_documentcollection_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL

    username = factory.Sequence(lambda n: "user_%s" % n)


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document

    title = factory.Sequence(lambda n: "Document {}".format(n))
    slug = factory.LazyAttribute(lambda o: slugify(o.title))


class DocumentCollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DocumentCollection

    title = factory.Sequence(lambda n: "DocumentCollection {}".format(n))
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
    user = factory.SubFactory(UserFactory)


class CollectionDirectoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CollectionDirectory

    user = factory.SubFactory(UserFactory)
    collection = factory.SubFactory(
        DocumentCollectionFactory, user=factory.SelfAttribute("..user")
    )
    depth = 1
    name = factory.Sequence(lambda n: "Document collection %s" % n)
