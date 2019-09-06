import json

from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import DetailView
from django.urls import reverse
from django.db.models import Q

from crossdomainmedia import CrossDomainMediaMixin

from . import get_document_model, get_documentcollection_model
from .models import Page
from .auth import DocumentCrossDomainMediaAuth
from .api_views import PageSerializer

Document = get_document_model()
DocumentCollection = get_documentcollection_model()


class DocumentView(DetailView):
    model = Document
    PREVIEW_PAGE_COUNT = 10

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.slug != self.kwargs.get('slug', ''):
            return redirect(self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        num_pages = self.object.num_pages
        try:
            start_from = int(self.request.GET.get('page', 1))
            if start_from > num_pages:
                raise ValueError
        except ValueError:
            start_from = 1
        pages = self.object.page_set.all()
        pages = pages.filter(number__gte=start_from)[:self.PREVIEW_PAGE_COUNT]
        ctx['pages'] = pages
        ctx['beta'] = (
            self.request.GET.get('beta') is not None and
            self.request.user.is_staff
        )
        serializer_klass = self.object.get_serializer_class()
        api_ctx = {
            'request': self.request
        }
        data = serializer_klass(self.object, context=api_ctx).data
        data['pages'] = PageSerializer(pages, many=True, context=api_ctx).data
        ctx['page'] = start_from
        ctx['document_data'] = json.dumps(data)
        return ctx

    def get_queryset(self):
        qs = super().get_queryset()
        cond = Q(public=True)
        if self.request.user.is_authenticated:
            cond |= Q(user=self.request.user)
        return qs.filter(cond)


class DocumentDCView(DocumentView):
    template_name = 'filingcabinet/dc/document_detail.html'


class PageTextView(DetailView):
    model = Document

    def get_object(self):
        return Page.objects.get(
            document_id=self.kwargs['pk'],
            number=int(self.kwargs['page'])
        )

    def render_to_response(self, context, **response_kwargs):
        obj = context['object']
        return HttpResponse(content=obj.content, content_type='text/plain')


class DocumentJSONView(DetailView):
    model = Document

    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)

    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(
            self.get_data(context),
            **response_kwargs
        )

    def get_data(self, context):
        obj = context['object']
        return {
            'title': obj.title,
            'description': obj.description,
            'id': obj.pk,
            'pages': obj.num_pages,
            'annotations': [
                # {
                #   title     : ANNOTATION_TITLE,
                #   page      : PAGE_INDEX,
                #   content   : ANNOTATION_DESCRIPTION
                #   location  : { image: "x1, y1, x2, y2" },
                # }
            ],
            'sections': [
                # { title     : CHAPTER_TITLE, pages: "1-10" },
                # { title     : CHAPTER_TITLE, pages: "11-20" }
            ],
            'resources': {
                'page': {
                    'text': reverse(
                        'document_page_text', kwargs={
                            'pk': obj.pk,
                            'page': 0
                        }).replace('/0/', '/{page}/'),
                    'image': obj.get_page_image_url_template()
                },
                # 'related_story': 'LINK_URL',
                'pdf': obj.get_file_url(),
                # 'search': 'SEARCH_UTILITY_URL'
            }
        }


class DocumentFileDetailView(CrossDomainMediaMixin, DetailView):
    '''
    Add the CrossDomainMediaMixin
    and set your custom media_auth_class
    '''
    media_auth_class = DocumentCrossDomainMediaAuth

    def get_object(self):
        return get_object_or_404(
            Document, uuid=self.kwargs['uuid']
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filename'] = self.kwargs['filename']
        return ctx

    def redirect_to_media(self, mauth):
        '''
        Force direct links on main domain that are not
        refreshing a token to go to the objects page
        '''
        # Check file authorization first
        url = mauth.get_authorized_media_url(self.request)

        # Check if download is requested
        download = self.request.GET.get('download')
        if download is None:
            # otherwise redirect to document page
            return redirect(self.object.get_absolute_url(), permanent=True)

        return redirect(url)

    def send_media_file(self, mauth):
        response = super().send_media_file(mauth)
        response['Link'] = '<{}>; rel="canonical"'.format(
            self.object.get_absolute_domain_url()
        )
        return response
