from django.test import TestCase
from django.urls import reverse

from filingcabinet.models import CollectionDirectory, CollectionDocument

from . import DocumentCollectionFactory, DocumentFactory, UserFactory


class DocumentCollectionDetailViewPaginationTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()

    def test_documentcollection_pagination(self):
        collection = DocumentCollectionFactory(user=self.user)
        for i in range(100):
            directory = CollectionDirectory(
                name=f"Directory {i}",
                user=self.user,
                collection=collection,
            )
            CollectionDirectory.add_root(instance=directory)

        for _ in range(100):
            document = DocumentFactory()
            CollectionDocument.objects.create(
                collection=collection,
                document=document,
            )

        url = reverse("api:documentcollection-detail", kwargs={"pk": collection.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Directories are not paginated, because there is no other endpoint to query them
        self.assertEqual(len(response.json()["directories"]), 100)

        # Document are paginated, because we have a seperate endpoint to query them
        self.assertEqual(len(response.json()["documents"]), 50)
