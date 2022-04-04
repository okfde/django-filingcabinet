from django.conf import settings
from django.template.defaultfilters import slugify
from django.test import TestCase
from django.urls import reverse

import factory

from filingcabinet import get_document_model, get_documentcollection_model

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


class DocumentCollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DocumentCollection

    title = factory.Sequence(lambda n: "DocumentCollection {}".format(n))
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
    user = factory.SubFactory(UserFactory)


class DocumentAccessTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()

    def test_unlisted_document_needs_slug(self):
        doc = DocumentFactory.create(user=self.user, public=True, listed=False)

        url = reverse(
            "filingcabinet:document-detail_short",
            kwargs={
                "pk": doc.pk,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        url = reverse(
            "filingcabinet:document-detail", kwargs={"pk": doc.pk, "slug": doc.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.user)
        url = reverse(
            "filingcabinet:document-detail_short",
            kwargs={
                "pk": doc.pk,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_list_unlisted_document_api(self):
        DocumentFactory.create(user=self.user, public=True, listed=False)
        url = reverse("api:document-list")
        response = self.client.get(url)
        self.assertEqual(len(response.json()), 0)
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(len(response.json()), 1)

    def test_retrieve_unlisted_document_api(self):
        doc = DocumentFactory.create(user=self.user, public=True, listed=False)
        url = reverse("api:document-detail", kwargs={"pk": doc.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        url = reverse("api:document-detail", kwargs={"pk": doc.pk})
        response = self.client.get(url + "?uid=" + str(doc.uid))
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_unlisted_documentcollection_needs_slug(self):
        collection = DocumentCollectionFactory.create(
            user=self.user, public=True, listed=False
        )

        url = reverse(
            "filingcabinet:document-collection_short",
            kwargs={
                "pk": collection.pk,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        url = reverse(
            "filingcabinet:document-collection",
            kwargs={"pk": collection.pk, "slug": collection.slug},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.user)
        url = reverse(
            "filingcabinet:document-collection_short",
            kwargs={
                "pk": collection.pk,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_list_unlisted_documentcollection_api(self):
        DocumentCollectionFactory.create(user=self.user, public=True, listed=False)
        url = reverse("api:documentcollection-list")
        response = self.client.get(url)
        self.assertEqual(len(response.json()), 0)
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(len(response.json()), 1)

    def test_retrieve_unlisted_documentcollection_api(self):
        collection = DocumentCollectionFactory.create(
            user=self.user, public=True, listed=False
        )
        url = reverse("api:documentcollection-detail", kwargs={"pk": collection.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        response = self.client.get(url + "?uid=" + str(collection.uid))
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
