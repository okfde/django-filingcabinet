from django.conf.urls import include
from django.contrib import admin
from django.urls import path

try:
    from fcdocs_annotate.annotation.api import FeatureViewSet
except ImportError:
    FeatureViewSet = None
from rest_framework.routers import DefaultRouter

from filingcabinet.api_views import (
    DocumentCollectionViewSet,
    DocumentViewSet,
    PageAnnotationViewSet,
    PageViewSet,
)

from . import admin as fc_admin  # noqa

api_router = DefaultRouter()

api_router.register(r"document", DocumentViewSet, basename="document")
api_router.register(
    r"documentcollection", DocumentCollectionViewSet, basename="documentcollection"
)
api_router.register(r"page", PageViewSet, basename="page")
api_router.register(r"pageannotation", PageAnnotationViewSet, basename="pageannotation")
if FeatureViewSet:
    api_router.register(r"feature", FeatureViewSet, basename="feature")


urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path(
            "documents/",
        ),
    ]
    + (
        [path("documents/features/", include("fcdocs_annotate.urls"))]
        if FeatureViewSet
        else []
    )
    + [
        path("api/", include((api_router.urls, "api"))),
    ]
)
