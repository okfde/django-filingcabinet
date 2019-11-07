from django.db.models import (
    Q, Value, BooleanField, Case, When
)

from django.template.defaultfilters import slugify

from rest_framework import (
    viewsets, mixins, serializers, permissions, filters, status
)
from rest_framework.response import Response

from . import get_document_model, get_documentcollection_model
from .models import Page, PageAnnotation

Document = get_document_model()


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
        source='get_file_url',
        read_only=True
    )
    cover_image = serializers.CharField(
        source='get_cover_image'
    )
    page_template = serializers.CharField(
        source='get_page_template'
    )

    class Meta:
        model = Document
        fields = (
            'resource_uri', 'id', 'site_url', 'title', 'description',
            'num_pages', 'public', 'allow_annotation', 'pending',
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
        model = Document
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


class PageAnnotationSerializer(serializers.HyperlinkedModelSerializer):
    document = serializers.HyperlinkedRelatedField(
        read_only=True,
        lookup_field='page.document_id',
        view_name='api:document-detail'
    )

    number = serializers.IntegerField(
        source='page.number',
        read_only=True
    )

    can_delete = serializers.BooleanField(read_only=True)

    class Meta:
        model = PageAnnotation
        fields = (
            'id', 'title', 'description',
            'top', 'left', 'width', 'height',
            'timestamp', 'can_delete',
            'highlight', 'image', 'document', 'number'
        )


def get_annotatable_documents(request):
    cond = Q(public=True, allow_annotation=True)
    if request.user.is_authenticated:
        cond |= Q(user=request.user)
    return Document.objects.filter(cond)


class CreatePageAnnotationSerializer(serializers.Serializer):
    document = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.none()
    )
    page_number = serializers.IntegerField()
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(
        allow_blank=True, max_length=1024
    )
    top = serializers.IntegerField(required=False, allow_null=True)
    left = serializers.IntegerField(required=False, allow_null=True)
    width = serializers.IntegerField(required=False, allow_null=True)
    height = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        fields = (
            'document', 'page_number',
            'title', 'description',
            'top', 'left', 'width', 'height',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = get_annotatable_documents(self.context['view'].request)
        self.fields['document'].queryset = qs

    def validate(self, data):
        """
        Check that start is before finish.
        """
        doc = data['document']
        if not (1 <= data['page_number'] <= doc.num_pages):
            raise serializers.ValidationError("page number out of bounds")
        page = Page.objects.get(
            document=data['document'],
            number=data['page_number']
        )
        if (not data.get('left') or not data.get('top')
                or not data.get('width') or not data.get('height')):
            return data

        MIN_DIM = 10
        MAX_WIDTH = page.width - data['left']
        MAX_HEIGHT = page.height - data['top']
        if (not (0 <= data['top'] <= page.height) or
                not (0 <= data['left'] <= page.width) or
                not (MIN_DIM <= data['width'] <= MAX_WIDTH) or
                not (MIN_DIM <= data['height'] <= MAX_HEIGHT)):
            raise serializers.ValidationError("selection incorrect")

        return data

    def create(self, validated_data):
        page = Page.objects.get(
            document=validated_data['document'],
            number=validated_data['page_number']
        )
        annotation = PageAnnotation.objects.create(
            page=page,
            title=validated_data['title'],
            description=validated_data['description'],
            top=validated_data.get('top'),
            left=validated_data.get('left'),
            width=validated_data.get('width'),
            height=validated_data.get('height'),
            user=validated_data['user'],
        )
        return annotation


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
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
        return Document.objects.filter(cond)


class PageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PageSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['content']

    def get_queryset(self):
        document_id = self.request.query_params.get('document', '')
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
        qs = Document.objects.filter(cond)
        qs = qs.prefetch_related('documents')
        return qs


class PageAnnotationViewSet(
        mixins.CreateModelMixin, mixins.DestroyModelMixin,
        mixins.ListModelMixin, mixins.RetrieveModelMixin,
        viewsets.GenericViewSet):
    serializer_class = PageAnnotationSerializer
    permission_classes = (IsUserOrReadOnly,)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePageAnnotationSerializer
        return self.serializer_class

    def get_base_queryset(self, document_id):
        cond = Q(public=True)
        if self.request.user.is_authenticated:
            cond |= Q(user=self.request.user)
        try:
            doc = Document.objects.filter(cond).get(pk=document_id)
        except (ValueError, Document.DoesNotExist):
            return PageAnnotation.objects.none()
        return PageAnnotation.objects.filter(page__document=doc)

    def annotate_permissions(self, qs):
        user = self.request.user

        if user.is_superuser:
            qs = qs.annotate(can_delete=Value(
                True, output_field=BooleanField())
            )
        else:
            whens = []
            if user.is_authenticated:
                whens = [When(user_id=user.id, then=Value(True))]

            qs = qs.annotate(
                can_delete=Case(
                    *whens,
                    default=Value(False),
                    output_field=BooleanField()
                )
            )
        return qs

    def get_queryset(self):
        document_id = self.request.query_params.get('document', '')

        qs = self.get_base_queryset(document_id)

        number = self.request.query_params.get('number')
        if number is not None:
            try:
                qs.filter(page__number=int(number))
            except ValueError:
                pass

        qs = self.annotate_permissions(qs)

        return qs.order_by('timestamp')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        data = {
            'status': 'success',
            'annotation': PageAnnotationSerializer(instance).data
        }
        return Response(data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)
