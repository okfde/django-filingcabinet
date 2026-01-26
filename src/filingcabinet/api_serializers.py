from django.template.defaultfilters import slugify

import markdown
import nh3
from rest_framework import serializers
from rest_framework.reverse import reverse

from . import get_document_model, get_documentcollection_model
from .models import (
    CollectionDirectory,
    DocumentPortal,
    Page,
    PageAnnotation,
)

Document = get_document_model()
DocumentCollection = get_documentcollection_model()


class PageSerializer(serializers.HyperlinkedModelSerializer):
    document = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="api:document-detail"
    )
    image = serializers.CharField(source="get_image_url")

    class Meta:
        model = Page
        fields = ("document", "number", "content", "width", "height", "image")


class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name="api:document-detail", lookup_field="pk"
    )
    site_url = serializers.CharField(source="get_absolute_domain_url", read_only=True)
    file_url = serializers.CharField(source="get_file_url", read_only=True)
    cover_image = serializers.CharField(source="get_cover_image")
    page_template = serializers.CharField(source="get_page_template")
    pages_uri = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "resource_uri",
            "id",
            "site_url",
            "title",
            "slug",
            "description",
            "published_at",
            "num_pages",
            "public",
            "listed",
            "allow_annotation",
            "pending",
            "file_url",
            "file_size",
            "cover_image",
            "page_template",
            "outline",
            "properties",
            "uid",
            "data",
            "pages_uri",
        )
        read_only_fields = (
            "slug",
            "published_at",
            "num_pages",
            "public",
            "listed",
            "allow_annotation",
            "pending",
            "file_size",
            "outline",
            "properties",
            "uid",
            "data",
        )

    def get_pages_uri(self, obj):
        extra = ""
        if not obj.listed:
            extra = "&uid={}".format(obj.uid)
        return "{}?document={}{}".format(reverse("api:page-list"), obj.id, extra)


class PagesMixin(object):
    def get_pages(self, obj):
        pages = obj.pages.all()
        serializer = PageSerializer(
            pages, many=True, context={"request": self.context["request"]}
        )
        return serializer.data


class DocumentDetailSerializer(PagesMixin, DocumentSerializer):
    pages = serializers.SerializerMethodField(source="get_pages")

    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + ("pages",)


class UpdateDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("title", "description")

    def update(self, instance, validated_data):
        if validated_data.get("title"):
            validated_data["slug"] = slugify(validated_data["title"])
        return super().update(instance, validated_data)


class CollectionDirectoryListSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()

    class Meta:
        model = CollectionDirectory
        fields = (
            "id",
            "name",
            "description",
            "depth",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "depth",
            "created_at",
            "updated_at",
        )

    def get_description(self, obj: CollectionDirectory) -> str:
        if not obj.description:
            return ""

        authorized_tags = {"p", "strong", "em", "ul", "ol", "li", "a"}

        html_output = markdown.markdown(obj.description)
        safe_html_output = nh3.clean(html_output, tags=authorized_tags)
        return safe_html_output


class CollectionDirectorySerializer(serializers.HyperlinkedModelSerializer):
    documents = DocumentSerializer(many=True, source="ordered_documents")
    directories = CollectionDirectoryListSerializer(many=True, source="get_children")

    class Meta:
        model = CollectionDirectory
        fields = (
            "id",
            "resource_uri",
            "name",
            "created_at",
            "updated_at",
            "documents",
            "directories",
        )
        read_only_fields = (
            "created_at",
            "updated_at",
        )


MAX_COLLECTION_DOCS = 50


class DocumentCollectionSerializer(serializers.HyperlinkedModelSerializer):
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name="api:documentcollection-detail", lookup_field="pk"
    )
    zip_download_url = serializers.CharField(
        source="get_zip_download_url", read_only=True
    )
    site_url = serializers.CharField(source="get_absolute_domain_url", read_only=True)
    cover_image = serializers.CharField(source="get_cover_image")
    document_count = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    document_directory_count = serializers.SerializerMethodField()
    documents_uri = serializers.SerializerMethodField()
    pages_uri = serializers.SerializerMethodField()
    current_directory = serializers.SerializerMethodField()
    directories = serializers.SerializerMethodField()
    directory_stack = serializers.SerializerMethodField()

    class Meta:
        model = get_documentcollection_model()
        fields = (
            "resource_uri",
            "id",
            "site_url",
            "title",
            "description",
            "public",
            "listed",
            "created_at",
            "updated_at",
            "document_count",
            "document_directory_count",
            "uid",
            "cover_image",
            "current_directory",
            "directories",
            "directory_stack",
            "documents",
            "documents_uri",
            "pages_uri",
            "settings",
            "zip_download_url",
        )
        read_only_fields = (
            "public",
            "listed",
            "created_at",
            "updated_at",
            "uid",
            "settings",
        )

    def get_document_count(self, obj):
        if hasattr(obj, "document_count"):
            return obj.document_count
        obj.document_count = obj.get_authenticated_documents(
            self.context["request"],
        ).count()
        return obj.document_count

    def get_document_directory_count(self, obj):
        parent = self.context.get("parent_directory")
        if hasattr(obj, "document_directory_count"):
            return obj.document_directory_count
        obj.document_directory_count = obj.get_authenticated_documents(
            self.context["request"], directory=parent
        ).count()
        return obj.document_directory_count

    def get_documents(self, obj):
        # Possibly prefetched in DocumentCollectionViewSet.get_queryset
        prefetched_docs = getattr(obj, "prefetched_documents", None)
        if prefetched_docs is not None:
            docs = prefetched_docs[:MAX_COLLECTION_DOCS]
        else:
            parent = self.context.get("parent_directory")
            docs = obj.get_authenticated_documents(
                self.context["request"], directory=parent
            )[:MAX_COLLECTION_DOCS]
        return Document.get_serializer_class()(
            docs, many=True, context=self.context
        ).data

    def get_documents_uri(self, obj):
        return "{}?collection={}&uid={}".format(
            reverse("api:document-list"), obj.id, obj.uid
        )

    def get_pages_uri(self, obj):
        return "{}?collection={}&uid={}".format(
            reverse("api:page-list"), obj.id, obj.uid
        )

    def get_current_directory(self, obj):
        parent = self.context.get("parent_directory")
        if parent:
            return CollectionDirectoryListSerializer(parent, context=self.context).data

    def get_directories(self, obj):
        directories = getattr(obj, "prefetched_directories", None)
        if directories is None:
            parent = self.context.get("parent_directory")
            directories = obj.get_directories(parent_directory=parent)
        return CollectionDirectoryListSerializer(
            directories, many=True, context=self.context
        ).data

    def get_directory_stack(self, obj):
        parent = self.context.get("parent_directory")
        if parent:
            directories = obj.get_parent_directories(parent)
            return CollectionDirectoryListSerializer(
                directories, many=True, context=self.context
            ).data
        else:
            return []


class PageAnnotationSerializer(serializers.HyperlinkedModelSerializer):
    document = serializers.HyperlinkedRelatedField(
        read_only=True, lookup_field="page.document_id", view_name="api:document-detail"
    )

    number = serializers.IntegerField(source="page.number", read_only=True)

    can_delete = serializers.BooleanField(read_only=True)

    class Meta:
        model = PageAnnotation
        fields = (
            "id",
            "title",
            "description",
            "top",
            "left",
            "width",
            "height",
            "timestamp",
            "can_delete",
            "highlight",
            "image",
            "document",
            "number",
        )
        read_only_fields = (
            "timestamp",
            "can_delete",
            "highlight",
            "image",
        )


# TODO: refactor this to a single serializer
class CreatePageAnnotationSerializer(serializers.Serializer):
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.none())
    page_number = serializers.IntegerField()
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True, max_length=1024)
    top = serializers.IntegerField(required=False, allow_null=True)
    left = serializers.IntegerField(required=False, allow_null=True)
    width = serializers.IntegerField(required=False, allow_null=True)
    height = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        fields = (
            "document",
            "page_number",
            "title",
            "description",
            "top",
            "left",
            "width",
            "height",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Document.get_annotatable(self.context["view"].request)
        self.fields["document"].queryset = qs

    def validate(self, data):
        """
        Check that start is before finish.
        """
        doc = data["document"]
        if not (1 <= data["page_number"] <= doc.num_pages):
            raise serializers.ValidationError("page number out of bounds")
        page = Page.objects.get(document=data["document"], number=data["page_number"])
        if (
            not data.get("left")
            or not data.get("top")
            or not data.get("width")
            or not data.get("height")
        ):
            return data

        MIN_DIM = 10
        MAX_WIDTH = page.width - data["left"]
        MAX_HEIGHT = page.height - data["top"]
        if (
            not (0 <= data["top"] <= page.height)
            or not (0 <= data["left"] <= page.width)
            or not (MIN_DIM <= data["width"] <= MAX_WIDTH)
            or not (MIN_DIM <= data["height"] <= MAX_HEIGHT)
        ):
            raise serializers.ValidationError("selection incorrect")

        return data

    def create(self, validated_data):
        page = Page.objects.get(
            document=validated_data["document"], number=validated_data["page_number"]
        )
        annotation = PageAnnotation.objects.create(
            page=page,
            title=validated_data["title"],
            description=validated_data["description"],
            top=validated_data.get("top"),
            left=validated_data.get("left"),
            width=validated_data.get("width"),
            height=validated_data.get("height"),
            user=validated_data["user"],
        )
        return annotation


class DocumentPortalSerializer(serializers.HyperlinkedModelSerializer):
    document_count = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    document_directory_count = serializers.SerializerMethodField()
    documents_uri = serializers.SerializerMethodField()
    pages_uri = serializers.SerializerMethodField()
    directories = serializers.SerializerMethodField()

    class Meta:
        model = DocumentPortal
        fields = (
            "id",
            "title",
            "description",
            "created_at",
            "document_count",
            "document_directory_count",
            "directories",
            "documents",
            "documents_uri",
            "pages_uri",
            "settings",
        )
        read_only_fields = (
            "created_at",
            "settings",
        )

    def get_document_count(self, obj):
        if hasattr(obj, "document_count"):
            return obj.document_count
        return obj.documents.all().count()

    def get_document_directory_count(self, obj):
        return self.get_document_count(obj)

    def get_documents(self, obj):
        docs = obj.documents.all()[:MAX_COLLECTION_DOCS]
        return Document.get_serializer_class()(
            docs, many=True, context=self.context
        ).data

    def get_documents_uri(self, obj):
        return "{}?portal={}".format(reverse("api:document-list"), obj.id)

    def get_pages_uri(self, obj):
        return "{}?portal={}".format(reverse("api:page-list"), obj.id)

    def get_directories(self, obj):
        return []
