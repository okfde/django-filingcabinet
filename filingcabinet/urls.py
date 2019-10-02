from django.conf.urls import url
from django.utils.translation import pgettext_lazy

from .views import (
    DocumentView, DocumentCollectionView
)

app_name = 'filingcabinet'

urlpatterns = [
    url(pgettext_lazy(
            'url part',
            r'^collection/(?P<pk>\d+)\-(?P<slug>[-\w]+)/$'
        ),
        DocumentCollectionView.as_view(), name='document-collection'),
    url(pgettext_lazy(
            'url part',
            r'^collection/(?P<pk>\d+)/$'
        ),
        DocumentCollectionView.as_view(), name='document-collection_short'),
    url(r"^(?P<pk>\d+)\-(?P<slug>[-\w]+)/$", DocumentView.as_view(),
        name="document-detail"),
    url(r"^(?P<pk>\d+)/$", DocumentView.as_view(),
        name="document-detail_short"),
]
