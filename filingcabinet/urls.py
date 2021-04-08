from django.urls import path
from django.utils.translation import pgettext_lazy
from django.views.decorators.clickjacking import xframe_options_exempt

from .views import (
    DocumentView, DocumentCollectionView,
    DocumentEmbedView, DocumentCollectionEmbedView
)

app_name = 'filingcabinet'

urlpatterns = [
    path(pgettext_lazy(
            'url part',
            'collection/<int:pk>-<slug:slug>/'
        ),
        DocumentCollectionView.as_view(), name='document-collection'),
    path(pgettext_lazy(
            'url part',
            'collection/<int:pk>/'
        ),
        DocumentCollectionView.as_view(), name='document-collection_short'),
    path(pgettext_lazy(
            'url part',
            'collection/<int:pk>-<slug:slug>/embed/',
        ),
        xframe_options_exempt(
            DocumentCollectionEmbedView.as_view()
        ),
        name="document-collection_embed"),
    path(pgettext_lazy(
            'url part',
            'collection/<int:pk>/embed/',
        ),
        xframe_options_exempt(
            DocumentCollectionEmbedView.as_view()
        ),
        name="document-collection_embed_short"),
    path("<int:pk>-<slug:slug>/", DocumentView.as_view(),
         name="document-detail"),
    path("<int:pk>/", DocumentView.as_view(),
         name="document-detail_short"),
    path("<int:pk>-<slug:slug>/embed/",
         xframe_options_exempt(
            DocumentEmbedView.as_view()
         ),
         name="document-detail_embed"),
    path("<int:pk>/embed/", xframe_options_exempt(
            DocumentEmbedView.as_view()
        ),
        name="document-detail_embed_short"),
]
