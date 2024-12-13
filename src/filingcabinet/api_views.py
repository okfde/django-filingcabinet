from django.db.models import BooleanField, Case, Count, Q, Value, When

from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import get_document_model, get_documentcollection_model
from .api_renderers import RSSRenderer
from .api_serializers import (
    CreatePageAnnotationSerializer,
    DocumentCollectionSerializer,
    DocumentDetailSerializer,
    DocumentSerializer,
    PageAnnotationSerializer,
    PageSerializer,
    UpdateDocumentSerializer,
)
from .api_utils import CustomLimitOffsetPagination, make_oembed_response
from .filters import DocumentFilter, PageDocumentFilterset
from .models import CollectionDirectory, Page, PageAnnotation

Document = get_document_model()
DocumentCollection = get_documentcollection_model()


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


class CanReadWritePermission(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.can_read(request)
        return obj.can_write(request)


class DocumentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_action_classes = {
        "list": DocumentSerializer,
        "retrieve": DocumentDetailSerializer,
        "update": UpdateDocumentSerializer,
    }
    pagination_class = CustomLimitOffsetPagination
    permission_classes = (CanReadWritePermission,)
    filterset_class = DocumentFilter

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return DocumentSerializer

    def can_read_unlisted_via_collection(self):
        query = self.request.GET.get("collection")
        if query and not query.isdigit():
            return False
        try:
            collection = DocumentCollection.objects.get(id=query)
        except DocumentCollection.DoesNotExist:
            return False
        return collection.can_read(self.request)

    def get_base_queryset(self):
        if self.action == "list" and not self.can_read_unlisted_via_collection():
            cond = Q(public=True, listed=True)
        else:
            cond = Q(public=True)
        if self.request.user.is_authenticated:
            cond |= Q(user=self.request.user)
        return Document.objects.filter(cond)

    def get_queryset(self):
        qs = self.get_base_queryset()
        if self.action == "list":
            qs = qs.filter(pending=False)
        return qs

    @action(detail=False, methods=["get"])
    def oembed(self, request):
        return make_oembed_response(request, Document)


class PageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PageSerializer
    filterset_class = PageDocumentFilterset
    renderer_classes = viewsets.GenericViewSet.renderer_classes + [RSSRenderer]
    pagination_class = CustomLimitOffsetPagination
    search_fields = ["content"]

    def get_queryset(self):
        document_id = self.request.query_params.get("document", "")
        collection_id = self.request.query_params.get("collection", "")

        if not document_id and not collection_id:
            return Page.objects.none()

        pages = Page.objects.all()

        if document_id:
            try:
                doc = Document.objects.get(pk=document_id)
                if not doc.can_read(self.request):
                    return Page.objects.none()
                pages = pages.filter(document=doc)
            except (ValueError, Document.DoesNotExist):
                return Page.objects.none()

        if collection_id:
            try:
                collection = DocumentCollection.objects.get(pk=collection_id)
                if not collection.can_read(self.request):
                    return Page.objects.none()
                pages = pages.filter(document__in=collection.documents.all())
            except (ValueError, DocumentCollection.DoesNotExist):
                return Page.objects.none()

        # Always order by publication date on RSS format
        has_query = self.request.GET.get("q")
        if has_query and self.request.GET.get("format") == "rss":
            pages = pages.order_by("-published_at")

        return pages.prefetch_related("document")


class DocumentCollectionViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_action_classes = {
        "list": DocumentCollectionSerializer,
    }
    permission_classes = (CanReadWritePermission,)
    pagination_class = CustomLimitOffsetPagination

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return DocumentCollectionSerializer

    def get_queryset(self):
        if self.action == "list":
            cond = Q(public=True, listed=True)
        else:
            cond = Q(public=True)
        if self.request.user.is_authenticated:
            cond |= Q(user=self.request.user)
        qs = DocumentCollection.objects.filter(cond)
        qs = qs.annotate(document_count=Count("documents"))
        # TODO: annotate doc count for directory for performance
        # qs = qs.annotate(document_directory_count=Count(
        #     'documents', filter=Q(filingcabinet)
        # ))
        qs = qs.prefetch_related("documents")
        return qs

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        ctx = super().get_serializer_context()
        if self.action != "retrieve":
            return ctx

        # FIXME: check if directory is part of this collection
        parent_directory = None
        try:
            # request is not available when called from manage.py generateschema
            if self.request is not None:
                dir_id = int(self.request.GET.get("directory", ""))
                parent_directory = CollectionDirectory.objects.get(id=dir_id)
        except (ValueError, CollectionDirectory.DoesNotExist):
            pass

        ctx.update({"parent_directory": parent_directory})
        return ctx

    @action(detail=False, methods=["get"])
    def oembed(self, request):
        return make_oembed_response(request, DocumentCollection)


class PageAnnotationViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PageAnnotationSerializer
    permission_classes = (IsUserOrReadOnly,)
    pagination_class = CustomLimitOffsetPagination

    def get_serializer_class(self):
        if self.action == "create":
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
        if not doc.can_read(self.request):
            return PageAnnotation.objects.none()
        return PageAnnotation.objects.filter(page__document=doc)

    def annotate_permissions(self, qs):
        user = self.request.user

        if user.is_superuser:
            qs = qs.annotate(can_delete=Value(True, output_field=BooleanField()))
        else:
            whens = []
            if user.is_authenticated:
                whens = [When(user_id=user.id, then=Value(True))]

            qs = qs.annotate(
                can_delete=Case(
                    *whens, default=Value(False), output_field=BooleanField()
                )
            )
        return qs

    def get_queryset(self):
        document_id = self.request.query_params.get("document", "")

        qs = self.get_base_queryset(document_id)

        number = self.request.query_params.get("number")
        if number is not None:
            try:
                qs.filter(page__number=int(number))
            except ValueError:
                pass

        qs = self.annotate_permissions(qs)

        return qs.order_by("timestamp")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        data = {
            "status": "success",
            "annotation": PageAnnotationSerializer(instance).data,
        }
        return Response(data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)
