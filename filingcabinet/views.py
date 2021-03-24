import json

from django.shortcuts import redirect, Http404
from django.urls import reverse
from django.views.generic import DetailView
from django.utils.translation import gettext as _
from django.templatetags.static import static

from . import get_document_model, get_documentcollection_model
from .api_views import PageSerializer
from .forms import get_viewer_preferences

Document = get_document_model()
DocumentCollection = get_documentcollection_model()

PREVIEW_PAGE_COUNT = 10


class PkSlugMixin:
    def get_redirect(self, obj):
        return redirect(obj)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.slug != self.kwargs.get('slug', ''):
            if self.object.can_read(request):
                # only redirect if we can access
                return self.get_redirect(self.object)
            raise Http404
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class AuthMixin:
    def get_queryset(self):
        return self.model.objects.get_authenticated_queryset(self.request)


def get_js_config(request, obj):
    return {
        'settings': {
            'canWrite': obj.can_write(request)
        },
        'resources': {
            'pdfjsWorker': static('js/pdf.worker.min.js')
        },
        'urls': {
            'pageApiUrl': reverse('api:page-list'),
            'documentApiUrl': reverse('api:document-list'),
            'pageAnnotationApiUrl': reverse('api:pageannotation-list'),
        },
        'i18n': {
            'loading': _('Loading...'),
            'page': _('page'),
            'pages': _('pages'),
            'one_match': _('one match'),
            'matches': _('matches'),
            'search': _('Search'),
            'searching': _('Searching...'),
            'found_on': _('Found on'),
            'found': _('found'),
            'show_text': _('Show/hide Text'),
            'title': _('Title'),
            'description': _('Description'),
            'cancel': _('Cancel'),
            'addAnnotation': _('Add annotation'),
            'deleteAnnotation': _('Delete this annotation?'),
            'backToCollection': _('Back to collection'),
            'documents': _('documents'),
        }
    }


def get_document_viewer_context(doc, request, page_number=1, defaults=None):
    pages = doc.pages.all()
    pages = pages.filter(number__gte=page_number)[:PREVIEW_PAGE_COUNT]

    ctx = {
        'object': doc,
        'pages': pages,
        'page_number': page_number,
        'defaults': json.dumps(defaults or {}),
        'config': json.dumps(get_js_config(request, doc))
    }
    serializer_klass = doc.get_serializer_class()
    api_ctx = {
        'request': request
    }
    data = serializer_klass(doc, context=api_ctx).data
    data['pages'] = PageSerializer(pages, many=True, context=api_ctx).data
    ctx['document_data'] = json.dumps(data)
    return ctx


class DocumentView(AuthMixin, PkSlugMixin, DetailView):
    model = Document
    template_name = 'filingcabinet/document_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        num_pages = self.object.num_pages
        try:
            start_from = int(self.request.GET.get('page', 1))
            if start_from > num_pages:
                raise ValueError
        except ValueError:
            start_from = 1
        ctx.update(get_document_viewer_context(
            self.object, self.request, page_number=start_from,
            defaults=get_viewer_preferences(self.request.GET)
        ))
        return ctx


class DocumentEmbedView(DocumentView):
    template_name = 'filingcabinet/document_detail_embed.html'

    def get_redirect(self, obj):
        return redirect('document-detail_embed', slug=obj.slug, pk=obj.pk)


def get_document_collection_context(collection, request):
    context = {
        'object': collection
    }
    context['documents'] = collection.ordered_documents
    serializer_klass = collection.get_serializer_class()
    api_ctx = {
        'request': request
    }
    data = serializer_klass(collection, context=api_ctx).data
    context['documentcollection_data'] = json.dumps(data)
    config = get_js_config(request, collection)
    context['config'] = json.dumps(config)
    return context


class DocumentCollectionView(AuthMixin, PkSlugMixin, DetailView):
    model = DocumentCollection
    template_name = 'filingcabinet/documentcollection_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            get_document_collection_context(self.object, self.request)
        )
        return context


class DocumentCollectionEmbedView(DocumentCollectionView):
    template_name = 'filingcabinet/documentcollection_detail_embed.html'

    def get_redirect(self, obj):
        return redirect('document-collection_embed', slug=obj.slug, pk=obj.pk)
