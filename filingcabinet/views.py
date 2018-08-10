from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.views.generic import DetailView
from django.urls import reverse

from . import get_document_model

from .models import Page

Document = get_document_model()


class DocumentView(DetailView):
    model = Document

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.slug and self.kwargs.get('slug') is None:
            return redirect(self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self):
        qs = super(DocumentView, self).get_queryset()
        return qs.filter(public=True)


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
