from django.db.models import Q
from django.template.defaultfilters import slugify

from rest_framework import viewsets, mixins, serializers, permissions

from . import get_document_model, get_documentcollection_model
from .models import Page


class PageSerializer(serializers.HyperlinkedModelSerializer):
    document = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='api:document-detail'
    )

    class Meta:
        model = Page
        fields = (
            'document', 'number', 'content',
            'width', 'height'
        )


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
        source='get_authorized_file_url',
        read_only=True
    )
    cover_image = serializers.CharField(
        source='get_cover_image'
    )
    page_template = serializers.CharField(
        source='get_page_template'
    )

    class Meta:
        model = get_document_model()
        fields = (
            'resource_uri', 'id', 'site_url', 'title', 'description',
            'num_pages', 'public', 'pending',
            'file_url', 'cover_image', 'page_template'
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


class UpdateDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_document_model()
        fields = ('title', 'description')

    def update(self, instance, validated_data):
        if validated_data.get('title'):
            validated_data['slug'] = slugify(validated_data['title'])
        return super().update(instance, validated_data)


class DocumentCollectionSerializer(serializers.HyperlinkedModelSerializer):
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='api:documentcollection-detail',
        lookup_field='pk'
    )
    site_url = serializers.CharField(
        source='get_absolute_domain_url',
        read_only=True
    )
    cover_image = serializers.CharField(
        source='get_cover_image'
    )
    documents = DocumentSerializer(
        many=True
    )

    class Meta:
        model = get_documentcollection_model()
        fields = (
            'resource_uri', 'id', 'site_url', 'title', 'description',
            'public', 'created_at', 'updated_at',
            'cover_image', 'documents',
        )


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if obj.user == request.user:
            return True

        if request.method in permissions.SAFE_METHODS:
            return obj.public

        return False


class DocumentViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    serializer_action_classes = {
        'list': DocumentSerializer,
        'retrieve': DocumentDetailSerializer,
        'update': UpdateDocumentSerializer
    }
    permission_classes = (IsUserOrReadOnly,)

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return DocumentSerializer

    def get_queryset(self):
        cond = Q(public=True)
        if self.request.user.is_authenticated:
            cond |= Q(user=self.request.user)
        return get_document_model().objects.filter(cond)


class PageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PageSerializer

    def get_queryset(self):
        document_id = self.request.query_params.get('document', '')
        Document = get_document_model()
        cond = Q(public=True)
        if self.request.user.is_authenticated:
            cond |= Q(user=self.request.user)
        try:
            doc = Document.objects.filter(cond).get(pk=document_id)
        except (ValueError, Document.DoesNotExist):
            return Page.objects.none()
        return Page.objects.filter(document=doc)


class DocumentCollectionViewSet(
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        viewsets.GenericViewSet):
    serializer_action_classes = {
        'list': DocumentCollectionSerializer,
    }
    permission_classes = (IsUserOrReadOnly,)

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return DocumentCollectionSerializer

    def get_queryset(self):
        cond = Q(public=True)
        if self.request.user.is_authenticated:
            cond |= Q(user=self.request.user)
        qs = get_document_model().objects.filter(cond)
        qs = qs.prefetch_related('documents')
        return qs
