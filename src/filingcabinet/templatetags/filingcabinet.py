import json

from django import template

from .. import get_document_model
from ..views import get_document_viewer_context, get_js_config

register = template.Library()
Document = get_document_model()


@register.inclusion_tag("filingcabinet/_document_viewer.html", takes_context=True)
def get_pdf_viewer(context, document: Document, page_number=1):
    request = context["request"]
    document_context = get_document_viewer_context(
        document, request, page_number=page_number
    )
    context.update(document_context)
    return context


@register.inclusion_tag(
    "filingcabinet/_documentcollection_viewer.html", takes_context=True
)
def get_document_list_viewer(context, collection_data):
    request = context["request"]

    context.update(
        {
            "documentcollection_data": json.dumps(collection_data),
            "config": json.dumps(get_js_config(request)),
        }
    )
    return context
