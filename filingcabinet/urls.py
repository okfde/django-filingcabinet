from django.conf import settings
from django.urls import path, re_path
from django.utils.translation import pgettext_lazy
from django.views.decorators.clickjacking import xframe_options_exempt

from .views import (
    DocumentCollectionEmbedView,
    DocumentCollectionView,
    DocumentEmbedView,
    DocumentFileDetailView,
    DocumentListEmbedView,
    DocumentListView,
    DocumentPortalEmbedView,
    DocumentPortalView,
    DocumentView,
)

app_name = "filingcabinet"

fc_urlpatterns = [
    path("", DocumentListView.as_view(), name="document-list"),
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
]


MEDIA_PATH = settings.MEDIA_URL
# Split off domain and leading slash
if MEDIA_PATH.startswith("http"):
    MEDIA_PATH = MEDIA_PATH.split("/", 3)[-1]
else:
    MEDIA_PATH = MEDIA_PATH[1:]


urlpatterns = fc_urlpatterns + [
    re_path(
        r"^%s%s/(?P<u1>[a-z0-9]{2})/(?P<u2>[a-z0-9]{2})/(?P<u3>[a-z0-9]{2})/(?P<uuid>[a-z0-9]{32})/(?P<filename>.+)"
        % (MEDIA_PATH, settings.FILINGCABINET_MEDIA_PRIVATE_PREFIX),
        DocumentFileDetailView.as_view(),
        name="filingcabinet-auth_document",
    )
]
