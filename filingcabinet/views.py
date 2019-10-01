import json

from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, get_object_or_404, Http404
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


class DocumentCollectionView(AuthMixin, PkSlugMixin, DetailView):
    model = DocumentCollection

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.slug and self.kwargs.get('slug') is None:
            return redirect(self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(public=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.object.documents.all()
        return context


class DocumentFileDetailView(CrossDomainMediaMixin, DetailView):
    '''
    Add the CrossDomainMediaMixin
    and set your custom media_auth_class
    '''
    media_auth_class = DocumentCrossDomainMediaAuth

    def get_object(self):
        uid = self.kwargs['uuid']
        if (
                uid[0:2] != self.kwargs['u1'] or
                uid[2:4] != self.kwargs['u2'] or
                uid[4:6] != self.kwargs['u3']):
            raise Http404
        return get_object_or_404(
            Document, uid=uid
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
