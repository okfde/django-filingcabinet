from django import template

from ..views import get_document_viewer_context

register = template.Library()


@register.simple_tag
def get_pdf_viewer_url(url, page_number=None):
    # Use native PDF viewer in iframe
    return url


@register.inclusion_tag("filingcabinet/_document_viewer.html", takes_context=True)
def get_pdf_viewer(context, document):
    request = context["request"]
    document_context = get_document_viewer_context(document, request)
    context.update(document_context)
    return context
