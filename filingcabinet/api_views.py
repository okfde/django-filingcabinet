from rest_framework import serializers
from rest_framework import viewsets

from . import get_document_model
from .models import Page


class PageSerializer(serializers.HyperlinkedModelSerializer):
    document = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='api:document-detail'
    )
    image_url = serializers.CharField(
        source='get_image_url'
    )

    class Meta:
        model = Page
        fields = (
            'document', 'number', 'content',
            'image_url'
        )

    def get_image_url(self, obj):
        return obj.get_image_url()


class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='api:document-detail',
        lookup_field='pk'
    )
    site_url = serializers.CharField(
        source='get_absolute_domain_url',
        read_only=True
    )
    file_url = serializers.CharField(
        source='get_file_url',
        read_only=True
    )
    cover_image = serializers.CharField(
        source='get_cover_image'
    )

    class Meta:
        model = get_document_model()
        fields = (
            'resource_uri', 'id', 'site_url', 'title', 'description',
            'num_pages',
            'file_url', 'cover_image',
        )


class PagesMixin(object):
    def get_pages(self, obj):
        pages = obj.page_set.all()
        serializer = PageSerializer(
            pages,
            many=True,
            context={'request': self.context['request']}
        )
        return serializer.data


class DocumentDetailSerializer(PagesMixin, DocumentSerializer):
    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + (
            'pages',
        )


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_action_classes = {
        'list': DocumentSerializer,
        'retrieve': DocumentDetailSerializer
    }
    queryset = get_document_model().objects.filter(public=True)

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return DocumentSerializer
