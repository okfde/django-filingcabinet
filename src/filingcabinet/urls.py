from django.urls import path
from django.utils.translation import pgettext_lazy
from django.views.decorators.clickjacking import xframe_options_exempt

from .views import (
    DocumentCollectionEmbedView,
    DocumentCollectionView,
    DocumentCollectionZipDownloadView,
    DocumentEmbedView,
    DocumentListEmbedView,
    DocumentPortalEmbedView,
    DocumentPortalView,
    DocumentView,
)

app_name = "filingcabinet"

fc_urlpatterns = [
    path(
        pgettext_lazy("url part", "embed/"),
        xframe_options_exempt(DocumentListEmbedView.as_view()),
        name="document-list_embed",
    ),
    path(
        pgettext_lazy("url part", "collection/<int:pk>-<slug:slug>/"),
        DocumentCollectionView.as_view(),
        name="document-collection",
    ),
    path(
        pgettext_lazy("url part", "collection/<int:pk>/"),
        DocumentCollectionView.as_view(),
        name="document-collection_short",
    ),
    path(
        pgettext_lazy(
            "url part",
            "collection/<int:pk>-<slug:slug>/embed/",
        ),
        xframe_options_exempt(DocumentCollectionEmbedView.as_view()),
        name="document-collection_embed",
    ),
    path(
        pgettext_lazy(
            "url part",
            "collection/<int:pk>/embed/",
        ),
        xframe_options_exempt(DocumentCollectionEmbedView.as_view()),
        name="document-collection_embed_short",
    ),
    path(
        pgettext_lazy("url part", "portal/<slug:slug>/"),
        DocumentPortalView.as_view(),
        name="document-portal",
    ),
    path(
        pgettext_lazy(
            "url part",
            "portal/<slug:slug>/embed/",
        ),
        xframe_options_exempt(DocumentPortalEmbedView.as_view()),
        name="document-portal_embed",
    ),
    path("<int:pk>-<slug:slug>/", DocumentView.as_view(), name="document-detail"),
    path("<int:pk>/", DocumentView.as_view(), name="document-detail_short"),
    path(
        "<int:pk>-<slug:slug>/embed/",
        xframe_options_exempt(DocumentEmbedView.as_view()),
        name="document-detail_embed",
    ),
    path(
        "<int:pk>/embed/",
        xframe_options_exempt(DocumentEmbedView.as_view()),
        name="document-detail_embed_short",
    ),
    path(
        pgettext_lazy("url part", "collection/<int:pk>/zip/"),
        DocumentCollectionZipDownloadView.as_view(),
        name="document-collection_zip_short",
    ),
    path(
        pgettext_lazy("url part", "collection/<int:pk>-<slug:slug>/zip/"),
        DocumentCollectionZipDownloadView.as_view(),
        name="document-collection_zip",
    ),
]

urlpatterns = fc_urlpatterns
