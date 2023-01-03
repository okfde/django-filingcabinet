from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path

from rest_framework.routers import DefaultRouter

from filingcabinet.api_views import (
    DocumentCollectionViewSet,
    DocumentViewSet,
    PageAnnotationViewSet,
    PageViewSet,
)
from filingcabinet.views import DocumentFileDetailView

from . import base_admin  # noqa

api_router = DefaultRouter()

api_router.register(r"document", DocumentViewSet, basename="document")
api_router.register(
    r"documentcollection", DocumentCollectionViewSet, basename="documentcollection"
)
api_router.register(r"page", PageViewSet, basename="page")
api_router.register(r"pageannotation", PageAnnotationViewSet, basename="pageannotation")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("documents/", include("filingcabinet.urls")),
    path("api/", include((api_router.urls, "api"))),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if not settings.DEBUG:
    MEDIA_PATH = settings.MEDIA_URL
    # Split off domain and leading slash
    if MEDIA_PATH.startswith("http"):
        MEDIA_PATH = MEDIA_PATH.split("/", 3)[-1]
    else:
        MEDIA_PATH = MEDIA_PATH[1:]

    urlpatterns += [
        re_path(
            r"^%s%s/(?P<u1>[a-z0-9]{2})/(?P<u2>[a-z0-9]{2})/(?P<u3>[a-z0-9]{2})/(?P<uuid>[a-z0-9]{32})/(?P<filename>.+)"
            % (MEDIA_PATH, settings.FILINGCABINET_MEDIA_PRIVATE_PREFIX),
            DocumentFileDetailView.as_view(),
            name="filingcabinet-auth_document",
        )
    ]
