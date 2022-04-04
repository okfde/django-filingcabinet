from django.conf.urls import include
from django.contrib import admin
from django.urls import path

from rest_framework.routers import DefaultRouter

from filingcabinet.api_views import (
    DocumentCollectionViewSet,
    DocumentViewSet,
    PageAnnotationViewSet,
    PageViewSet,
)

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
]
