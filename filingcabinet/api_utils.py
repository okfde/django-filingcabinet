from django.conf import settings

from rest_framework import status
from rest_framework.response import Response


def make_oembed_response(request, model):
    format = request.GET.get("format")
    if format is not None and format != "json":
        return Response({}, status=status.HTTP_501_NOT_IMPLEMENTED)
    url = request.GET.get("url")
    obj = model.objects.get_public_via_url(url)
    if obj is None:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    DUMMY = 999999
    try:
        max_width = int(request.GET.get("maxwidth", DUMMY))
        max_height = int(request.GET.get("maxheight", DUMMY))
    except ValueError:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)
    if max_width == DUMMY:
        width = "100%"
    else:
        width = "{}px".format(min(640, max_width))
    if max_height == DUMMY:
        height = "80vh"
    else:
        height = "{}px".format(min(640, max_height))
    iframe_url = obj.get_absolute_domain_embed_url()
    return Response(
        {
            "version": "1.0",
            "type": "rich",
            "provider_name": getattr(settings, "SITE_NAME", ""),
            "provider_url": getattr(settings, "SITE_URL", ""),
            "width": width,
            "height": height,
            "title": obj.title,
            "html": """
<iframe style="width:{width};border:0;height:{height}"
src="{url}?maxHeight={height}"></iframe>
        """.format(
                url=iframe_url, height=height, width=width
            ).strip(),
        }
    )
