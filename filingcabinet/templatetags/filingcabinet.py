from django import template

register = template.Library()


@register.simple_tag
def get_pdf_viewer(url, page_number=None):
    # Use native PDF viewer in iframe
    return url
