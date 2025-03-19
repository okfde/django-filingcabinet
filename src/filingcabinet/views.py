import json
import os.path
from collections import defaultdict
from pathlib import Path
from typing import override

from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import (
    Http404,
    get_object_or_404,
    redirect,
)
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import DetailView, TemplateView

import zipstream

from . import get_document_model, get_documentcollection_model
from .api_views import PageSerializer
from .forms import get_viewer_preferences
from .models import CollectionDirectory, CollectionDocument, DocumentPortal
from .settings import FILINGCABINET_ENABLE_WEBP, FILINGCABINET_MEDIA_PRIVATE_INTERNAL

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
            "documentApiUrl": reverse("api:document-list"),
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
            "showText": _("Show/hide Text"),
            "title": _("Title"),
            "description": _("Description"),
            "cancel": _("Cancel"),
            "addAnnotation": _("Add annotation"),
            "deleteAnnotation": _("Delete this annotation?"),
            "backToCollection": _("Back"),
            "documents": _("documents"),
            "areShown": _("are shown"),
            "downloadPDF": _("Download PDF"),
            "downloadZIP": _("Download ZIP"),
            "info": _("Document Info"),
            "author": _("Author"),
            "publicationDate": _("publication date"),
            "creator": _("Creator"),
            "producer": _("producer"),
            "url": _("URL"),
            "copyDocumentLink": _("Copy document URL"),
            "copyCollectionLink": _("Copy link to collection"),
            "copied": _("Copied!"),
            "copyFailed": _("Failed to copy"),
            "zoomIn": _("Zoom in"),
            "zoomOut": _("Zoom out"),
            "annotations": _("Annotations"),
            "showSearchbar": _("Show Searchbar"),
            "showAnnotations": _("Show Annotations"),
            "hideAnnotations": _("Hide Annotations"),
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
    try:
        dir_id = request.GET.get("directory")
        context["parent_directory"] = api_ctx["parent_directory"] = (
            CollectionDirectory.objects.get(id=dir_id, collection=collection)
        )
    except (ValueError, CollectionDirectory.DoesNotExist):
        pass

    data = serializer_klass(collection, context=api_ctx).data
    context["documentcollection_data"] = json.dumps(data)
    config = get_js_config(request, collection)
    config["deepUrls"] = True
    context["config"] = json.dumps(config)
    return context


class DocumentCollectionView(AuthMixin, PkSlugMixin, DetailView):
    model = DocumentCollection
    template_name = "filingcabinet/documentcollection_detail.html"
    redirect_url_name = "filingcabinet:document-collection"
    redirect_short_url_name = "filingcabinet:document-collection_short"

    @override
    def get(self, request, *args, **kwargs):
        if "document" in request.GET:
            try:
                CollectionDocument.objects.get(
                    document_id=request.GET.get("document"), collection_id=kwargs["pk"]
                )
            except (CollectionDocument.DoesNotExist, ValueError):
                # drop the query params
                return redirect(request.path)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(get_document_collection_context(self.object, self.request))
        return context


async def as_aiter(iter):
    for i in iter:
        yield i


class ZipStreamResponse(StreamingHttpResponse):
    @property
    def streaming_content(self):
        return self._sc

    @streaming_content.setter
    def streaming_content(self, value):
        self._sc = value

    def __iter__(self):
        return iter(self._sc)

    def __aiter__(self):
        return as_aiter(iter(self._sc))


class DocumentCollectionZipDownloadView(AuthMixin, PkSlugMixin, DetailView):
    model = DocumentCollection
    redirect_url_name = "filingcabinet:document-collection_zip"
    redirect_short_url_name = "filingcabinet:document-collection_zip_short"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(get_document_collection_context(self.object, self.request))
        return context

    def render_to_response(self, context):
        if "parent_directory" in context:
            root_directory = context["parent_directory"]
            descendants = root_directory.get_descendants()
            coll_docs = CollectionDocument.objects.filter(
                collection=self.object,
                document__pending=False,
                directory__in=[*descendants, root_directory],
            )
            max_depth = root_directory.depth + 1  # exclude current directory
        else:
            root_directory = None
            coll_docs = CollectionDocument.objects.filter(
                collection=self.object, document__pending=False
            )
            max_depth = 0

        archive_stream = zipstream.ZipFile(mode="w", allowZip64=True)

        directory_dirname_map = {}
        filename_counter = defaultdict(int)
        for doc in coll_docs:
            _, doc_ext = os.path.splitext(doc.document.get_file_path())
            doc_filename_stem = (
                doc.document.title.replace("/", "_").replace("\\", "_").strip()
            )
            if not doc_filename_stem:
                doc_filename_stem = "unnamed"
            doc_filename = doc_filename_stem + doc_ext
            if doc.directory is not None and doc.directory != root_directory:
                if doc.directory.pk not in directory_dirname_map:
                    path_to_root = doc.directory.get_path_to_root(max_depth)
                    dirname = os.path.join(*path_to_root)
                    directory_dirname_map[doc.directory.pk] = dirname
                else:
                    dirname = directory_dirname_map[doc.directory.pk]
                filename = os.path.join(
                    dirname,
                    doc_filename,
                )
            else:
                filename = doc_filename
            archive_stream.write(
                doc.document.get_file_path(),
                arcname=ensure_unique_filename(filename_counter, filename),
            )

        resp = ZipStreamResponse(
            archive_stream,
            content_type="application/zip",
        )
        resp["Content-Disposition"] = f'attachment; filename="{self.object.slug}.zip"'
        return resp


def ensure_unique_filename(filename_counter: defaultdict, filename: str):
    if filename_counter[filename] > 0:
        original_path = Path(filename)
        original_filename = filename
        while filename_counter[filename] > 0:
            filename = str(
                original_path.with_name(
                    original_path.stem
                    + "-"
                    + str(filename_counter[original_filename])
                    + original_path.suffix
                )
            )
            filename_counter[original_filename] += 1

    filename_counter[filename] += 1
    return filename


class DocumentCollectionEmbedView(DocumentCollectionView):
    template_name = "filingcabinet/documentcollection_detail_embed.html"
    redirect_url_name = "filingcabinet:document-collection_embed"
    redirect_short_url_name = "filingcabinet:document-collection_embed_short"


class DocumentCollectionDownloadView(DocumentCollectionView):
    template_name = "filingcabinet/documentcollection_detail_download.html"
    redirect_url_name = "filingcabinet:document-collection_download"
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
    objs = Document.objects.filter(pending=False, public=True)
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


class DocumentFileDetailView(AuthMixin, DetailView):
    model = Document

    def get_object(self):
        uid = self.kwargs["uuid"]
        if (
            uid[0:2] != self.kwargs["u1"]
            or uid[2:4] != self.kwargs["u2"]
            or uid[4:6] != self.kwargs["u3"]
        ):
            raise Http404
        return get_object_or_404(self.get_queryset(), uid=uid)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        url = self.object.get_file_name(filename=self.kwargs["filename"])
        url = FILINGCABINET_MEDIA_PRIVATE_INTERNAL + url
        response = HttpResponse()
        # Content-Type is filled in by nginx
        response["Content-Type"] = ""
        response["X-Accel-Redirect"] = url
        return response
