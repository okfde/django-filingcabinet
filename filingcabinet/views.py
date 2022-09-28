import json

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import Http404, get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import DetailView, TemplateView

from . import get_document_model, get_documentcollection_model
from .api_views import PageSerializer
from .forms import get_viewer_preferences
from .models import DocumentPortal
from .settings import FILINGCABINET_ENABLE_WEBP

Document = get_document_model()
DocumentCollection = get_documentcollection_model()

PREVIEW_PAGE_COUNT = 10


class PkSlugMixin:
    def get_redirect(self, obj):
        if obj.slug:
            url = reverse(
                self.redirect_url_name, kwargs={"slug": obj.slug, "pk": obj.pk}
            )
        else:
            url = reverse(self.redirect_short_url_name, kwargs={"pk": obj.pk})
        query = self.request.META["QUERY_STRING"]
        if query:
            return redirect("{}?{}".format(url, query))
        return redirect(url)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.slug != self.kwargs.get("slug", ""):
            if self.object.can_read(request):
                # only redirect if we can access
                return self.get_redirect(self.object)
            raise Http404
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class AuthMixin:
    def get_queryset(self):
        return self.model.objects.get_authenticated_queryset(self.request)


def get_js_config(request, obj=None):
    context = {
        "urls": {
            "pageAnnotationApiUrl": reverse("api:pageannotation-list"),
        },
        "i18n": {
            "loading": _("Loading..."),
            "loadMore": _("Load more"),
            "page": _("page"),
            "pages": _("pages"),
            "one_match": _("one match"),
            "matches": _("matches"),
            "search": _("Search"),
            "clear": _("Clear"),
            "searchTerm": _("Search term"),
            "searching": _("Searching..."),
            "found_on": _("Found on"),
            "found": _("found"),
            "clearSearch": _("clear search"),
            "searchingInDirectory": _("searched in directory"),
            "show_text": _("Show/hide Text"),
            "title": _("Title"),
            "description": _("Description"),
            "cancel": _("Cancel"),
            "addAnnotation": _("Add annotation"),
            "deleteAnnotation": _("Delete this annotation?"),
            "backToCollection": _("Back"),
            "documents": _("documents"),
            "areShown": _("are shown"),
            "downloadPDF": _("Download PDF"),
            "info": _("Document Info"),
            "author": _("Author"),
            "publicationDate": _("publication date"),
            "creator": _("Creator"),
            "producer": _("producer"),
            "url": _("URL"),
        },
    }

    if obj is not None:
        context.update({"settings": {"canWrite": obj.can_write(request)}})
    return context


def get_document_viewer_context(doc, request, page_number=1, defaults=None):
    if defaults is None:
        defaults = {}

    if FILINGCABINET_ENABLE_WEBP and not doc.has_format_webp() and not doc.pending:
        from .tasks import convert_images_to_webp_task

        convert_images_to_webp_task.delay(doc.pk)

    pages = doc.pages.all()
    pages = pages.filter(number__gte=page_number)[:PREVIEW_PAGE_COUNT]
    has_more = page_number + PREVIEW_PAGE_COUNT - 1 < doc.num_pages
    ctx = {
        "object": doc,
        "pages": pages,
        "next_page": page_number + PREVIEW_PAGE_COUNT if has_more else None,
        "page_number": page_number,
        "defaults": json.dumps(defaults),
        "config": json.dumps(get_js_config(request, doc)),
        "maxHeight": defaults.get("maxHeight"),
    }
    serializer_klass = doc.get_serializer_class()
    api_ctx = {"request": request}
    data = serializer_klass(doc, context=api_ctx).data
    data["pages"] = PageSerializer(pages, many=True, context=api_ctx).data
    ctx["document_data"] = json.dumps(data)
    return ctx


class DocumentView(AuthMixin, PkSlugMixin, DetailView):
    model = Document
    template_name = "filingcabinet/document_detail.html"
    redirect_url_name = "filingcabinet:document-detail"
    redirect_short_url_name = "filingcabinet:document-detail_short"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        num_pages = self.object.num_pages
        try:
            start_from = int(self.request.GET.get("page", 1))
            if start_from > num_pages:
                raise ValueError
        except ValueError:
            start_from = 1
        ctx.update(
            get_document_viewer_context(
                self.object,
                self.request,
                page_number=start_from,
                defaults=get_viewer_preferences(self.request.GET),
            )
        )
        return ctx


class DocumentEmbedView(DocumentView):
    template_name = "filingcabinet/document_detail_embed.html"
    redirect_url_name = "filingcabinet:document-detail_embed"
    redirect_short_url_name = "filingcabinet:document-detail_embed_short"


def get_document_collection_context(collection, request):
    context = {"object": collection}
    context["documents"] = collection.ordered_documents
    serializer_klass = collection.get_serializer_class()
    api_ctx = {"request": request}
    data = serializer_klass(collection, context=api_ctx).data
    context["documentcollection_data"] = json.dumps(data)
    config = get_js_config(request, collection)
    context["config"] = json.dumps(config)
    return context


class DocumentCollectionView(AuthMixin, PkSlugMixin, DetailView):
    model = DocumentCollection
    template_name = "filingcabinet/documentcollection_detail.html"
    redirect_url_name = "filingcabinet:document-collection"
    redirect_short_url_name = "filingcabinet:document-collection_short"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(get_document_collection_context(self.object, self.request))
        return context


class DocumentCollectionEmbedView(DocumentCollectionView):
    template_name = "filingcabinet/documentcollection_detail_embed.html"
    redirect_url_name = "filingcabinet:document-collection_embed"
    redirect_short_url_name = "filingcabinet:document-collection_embed_short"


def get_document_portal_context(portal, request):
    context = {"object": portal}
    context["documents"] = Document.objects.filter(portal=portal, pending=False)
    serializer_klass = portal.get_serializer_class()
    api_ctx = {"request": request}
    data = serializer_klass(portal, context=api_ctx).data
    context["documentcollection_data"] = json.dumps(data)
    config = get_js_config(request, portal)
    context["config"] = json.dumps(config)
    return context


class DocumentPortalView(DetailView):
    template_name = "filingcabinet/documentportal_detail.html"
    redirect_url_name = "filingcabinet:document-portal"
    redirect_short_url_name = "filingcabinet:document-portal_short"

    def get_queryset(self):
        if self.request.user.is_superuser:
            return DocumentPortal.objects.all()
        return DocumentPortal.objects.filter(public=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(get_document_portal_context(self.object, self.request))
        return context


class DocumentPortalEmbedView(DocumentPortalView):
    template_name = "filingcabinet/documentcollection_detail_embed.html"
    redirect_url_name = "filingcabinet:document-portal_embed"
    redirect_short_url_name = "filingcabinet:document-portal_embed_short"


def get_document_list_context(request):
    context = {
        "object": {
            "title": _("All documents"),
        }
    }
    objs = Document.objects.filter(pending=False)
    context["documents"] = objs
    context["documentcollection_data"] = json.dumps(
        {
            "documents": [],
            "document_directory_count": objs.count(),
            "document_count": objs.count(),
            "documents_uri": reverse("api:document-list"),
            "pages_uri": reverse("api:page-list"),
            "directories": [],
        }
    )
    config = get_js_config(request)
    context["config"] = json.dumps(config)
    return context


class DocumentListView(TemplateView):
    template_name = "filingcabinet/document_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(get_document_list_context(self.request))
        return context


class DocumentListEmbedView(DocumentListView):
    template_name = "filingcabinet/documentcollection_detail_embed.html"


class DocumentFileDetailView(DetailView):
    def get_object(self):
        uid = self.kwargs["uuid"]
        if (
            uid[0:2] != self.kwargs["u1"]
            or uid[2:4] != self.kwargs["u2"]
            or uid[4:6] != self.kwargs["u3"]
        ):
            raise Http404
        return get_object_or_404(Document, uid=uid)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        url = self.object.get_file_name(filename=self.kwargs["filename"])
        url = settings.FILINGCABINET_MEDIA_PRIVATE_INTERNAL + url
        print(url)
        response = HttpResponse()
        # Content-Type is filled in by nginx
        response["Content-Type"] = ""
        response["X-Accel-Redirect"] = url
        return response
