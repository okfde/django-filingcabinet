from django.conf.urls import include
from django.urls import path

try:
    from fcdocs_annotate.annotation.api import FeatureViewSet
except ImportError:
    FeatureViewSet = None

from .base_urls import api_router
from .base_urls import urlpatterns as base_urlpatterns

if FeatureViewSet:
    api_router.register(r"feature", FeatureViewSet, basename="feature")


urlpatterns = (
    base_urlpatterns
    + [path("documents/features/", include("fcdocs_annotate.annotation.urls"))]
    if FeatureViewSet
    else []
)
