from django import template

from .. import get_document_model
from ..views import get_document_viewer_context

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
