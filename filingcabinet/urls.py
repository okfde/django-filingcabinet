from django.conf.urls import url

from .views import (
    DocumentView, DocumentDCView, DocumentJSONView, PageTextView
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
