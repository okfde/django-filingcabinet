from django_filters import rest_framework as filters


from . import get_document_model, get_documentcollection_model
from .models import CollectionDirectory

Document = get_document_model()
DocumentCollection = get_documentcollection_model()

NULL_VALUE = '-'


class DocumentFilter(filters.FilterSet):
    directory = filters.ModelChoiceFilter(
        queryset=(
            CollectionDirectory.objects.all()
            .select_related('collection')
        ),
        null_label='',
        null_value=NULL_VALUE,
        method='filter_directory',
    )
    collection = filters.ModelChoiceFilter(
        queryset=DocumentCollection.objects.all(),
        method='filter_collection',
    )
    ids = filters.CharFilter(
        method='filter_ids'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = kwargs.get('request')
        if request is None:
            request = self.view.request
        self.request = request

    def filter_ids(self, qs, name, value):
        try:
            ids = [
                int(x) for x in value.split(',') if x
            ]
        except ValueError:
            ids = None
        if ids:
            qs = qs.filter(id__in=ids)
        return qs

    def filter_directory(self, qs, name, directory):
        if NULL_VALUE == directory:
            return qs.filter(
                filingcabinet_collectiondocument__directory__isnull=True
            )
        if not directory.collection.can_read(self.request):
            return qs.none()
        return qs.filter(
            filingcabinet_collectiondocument__directory=directory
        ).order_by(
            'filingcabinet_collectiondocument__order'
        )

    def filter_collection(self, qs, name, collection):
        if not collection.can_read(self.request):
            return qs.none()
        return qs.filter(
            filingcabinet_collectiondocument__collection=collection
        ).order_by(
            'filingcabinet_collectiondocument__order'
        )
