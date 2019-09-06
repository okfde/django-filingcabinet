from django.conf.urls import url
from django.conf import settings
from django.utils.translation import pgettext_lazy

from .views import (
    DocumentView, DocumentDCView, DocumentJSONView, PageTextView,
    DocumentFileDetailView
)

app_name = 'filingcabinet'

urlpatterns = [
    url(r"^(?P<pk>\d+)\-(?P<slug>[-\w]+)/$", DocumentView.as_view(),
        name="document-detail"),
    url(r"^(?P<pk>\d+)/$", DocumentView.as_view(),
        name="document-detail_short"),
    url(r"^(?P<pk>\d+)\.json$", DocumentJSONView.as_view(),
        name="document_json"),
    url(r"^(?P<pk>\d+)/dc/$", DocumentDCView.as_view(),
        name="document-detail_dc"),
    url(r"^(?P<pk>\d+)/text/(?P<page>\d+)/$", PageTextView.as_view(),
        name="document_page_text"),
]


MEDIA_PATH = settings.MEDIA_URL
# Split off domain and leading slash
if MEDIA_PATH.startswith('http'):
    MEDIA_PATH = MEDIA_PATH.split('/', 3)[-1]
else:
    MEDIA_PATH = MEDIA_PATH[1:]


urlpatterns += [
    url(r'^%s%s/[a-z0-9]{2}/[a-z0-9]{2}/[a-z0-9]{2}/(?P<uuid>[a-z0-9]{32})/(?P<filename>.+)' % (
        MEDIA_PATH, settings.FILINGCABINET_MEDIA_PRIVATE_PREFIX
    ), DocumentFileDetailView.as_view(), name='filingcabinet-auth_document')
]
