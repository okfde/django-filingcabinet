import re

from django.utils.translation import gettext as _

from feedgen.feed import FeedGenerator
from rest_framework import renderers

from . import get_document_model

CONTROLCHARS_RE = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]")


def clean_feed_output(output):
    return CONTROLCHARS_RE.sub("", output)


def get_doc_id(item):
    return int(item["document"].rsplit("/", 2)[1])


class RSSRenderer(renderers.BaseRenderer):
    """
    Renderer which serializes to CustomXML.
    """

    media_type = "application/xml"
    format = "rss"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders *data* into serialized XML.
        """
        if data is None:
            return ""

        Document = get_document_model()

        request = renderer_context["request"]
        fg = FeedGenerator()
        feed_url = request.build_absolute_uri()
        feed_title = _("Document feed")
        feed_description = _("Feed for document search")

        fg.id(feed_url)
        fg.title(feed_title)
        fg.subtitle(feed_description)
        fg.link(href=feed_url, rel="self")
        fg.generator("")
        objects = data.get("objects", [])
        doc_ids = [get_doc_id(item) for item in objects]
        doc_map = {d.id: d for d in Document.objects.filter(id__in=doc_ids)}

        for item in reversed(objects):
            doc_id = get_doc_id(item)
            doc = doc_map[doc_id]
            fe = fg.add_entry()
            url = "{}?page={}".format(doc.get_absolute_domain_url(), item["number"])
            fe.id(url)
            fe.pubDate(doc.published_at or doc.created_at)
            fe.title(_("{} (p. {})").format(doc.title, item["number"]))
            fe.link({"href": url})
            if "query_highlight" in item:
                fe.content(
                    content=clean_feed_output(item["query_highlight"]), type="html"
                )
            else:
                fe.description(clean_feed_output(item["content"]))

        return fg.rss_str(pretty=True)
