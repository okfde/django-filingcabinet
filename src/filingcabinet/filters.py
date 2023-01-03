from django.db.models import Q

from django_filters import rest_framework as filters
from taggit.models import Tag

from . import get_document_model, get_documentcollection_model
from .models import CollectionDirectory, DocumentPortal, Page

Document = get_document_model()
DocumentCollection = get_documentcollection_model()

NULL_VALUE = "-"


class DocumentFilter(filters.FilterSet):
    directory = filters.ModelChoiceFilter(
        queryset=(CollectionDirectory.objects.all().select_related("collection")),
        null_label="",
        null_value=NULL_VALUE,
        method="filter_directory",
    )
    collection = filters.ModelChoiceFilter(
        queryset=DocumentCollection.objects.all(),
        method="filter_collection",
    )
    portal = filters.ModelChoiceFilter(
        queryset=DocumentPortal.objects.filter(public=True),
        to_field_name="pk",
        method="filter_portal",
    )
    tag = filters.ModelChoiceFilter(
        queryset=Tag.objects.all(), to_field_name="slug", method="filter_tag"
    )
    ids = filters.CharFilter(method="filter_ids")
    created_at = filters.DateFromToRangeFilter(
        method="filter_created_at",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = kwargs.get("request")
        if request is None:
            request = self.view.request
        self.request = request

    def filter_ids(self, qs, name, value):
        try:
            ids = [int(x) for x in value.split(",") if x]
        except ValueError:
            ids = None
        if ids:
            qs = qs.filter(id__in=ids)
        return qs

    def filter_directory(self, qs, name, directory):
        if NULL_VALUE == directory:
            return qs.filter(filingcabinet_collectiondocument__directory__isnull=True)
        if not directory.collection.can_read(self.request):
            return qs.none()
        return qs.filter(
            filingcabinet_collectiondocument__directory=directory
        ).order_by("filingcabinet_collectiondocument__order")

    def filter_collection(self, qs, name, collection):
        if not collection.can_read(self.request):
            return qs.none()

        qs = qs.filter(
            filingcabinet_collectiondocument__collection=collection
        ).order_by("filingcabinet_collectiondocument__order")
        data_filters = collection.settings.get("filters", [])
        qs = self.apply_data_filters(qs, data_filters)
        return qs

    def filter_portal(self, qs, name, portal):
        qs = qs.filter(portal=portal)
        qs = self.apply_data_filters(qs, portal.settings.get("filters", []))
        return qs

    def filter_tag(self, qs, name, value):
        return qs.filter(tags__slug=value)

    def apply_data_filters(self, qs, filters):
        for filt in filters:
            if not filt["key"].startswith("data."):
                continue
            val = self.request.GET.get(filt["key"])
            if not val:
                continue
            data_type = filt.get("datatype")
            if data_type:
                try:
                    if data_type == "int":
                        val = int(val)
                except ValueError:
                    continue
            filt_key = filt["key"].replace(".", "__")
            qs = qs.filter(**{filt_key: val})
        return qs

    def filter_created_at(self, qs, name, value):
        range_kwargs = {}
        if value.start is not None:
            range_kwargs["gte"] = value.start
        if value.stop is not None:
            range_kwargs["lte"] = value.stop

        for comp, val in range_kwargs.items():
            qs = qs.filter(
                Q(
                    **{
                        "published_at__isnull": False,
                        "published_at__{}".format(comp): val,
                    }
                )
                | Q(
                    **{"published_at__isnull": True, "created_at__{}".format(comp): val}
                )
            )
        return qs


class PageDocumentFilterset(filters.FilterSet):
    q = filters.CharFilter(field_name="content", lookup_expr="contains")

    tag = filters.ModelChoiceFilter(
        queryset=Tag.objects.all(), to_field_name="slug", method="filter_tag"
    )
    collection = filters.ModelChoiceFilter(
        queryset=DocumentCollection.objects.all(),
        to_field_name="pk",
        method="filter_collection",
    )
    directory = filters.ModelChoiceFilter(
        queryset=(CollectionDirectory.objects.all().select_related("collection")),
        null_label="",
        null_value=NULL_VALUE,
        method="filter_directory",
    )
    portal = filters.ModelChoiceFilter(
        queryset=DocumentPortal.objects.filter(public=True),
        to_field_name="pk",
        method="filter_portal",
    )
    document = filters.ModelChoiceFilter(
        queryset=Document.objects.all(),
        to_field_name="pk",
        method="filter_document",
    )
    number = filters.NumberFilter(field_name="number", lookup_expr="exact")

    created_at = filters.DateFromToRangeFilter(
        method="filter_created_at",
    )

    class Meta:
        model = Page
        fields = ["q", "tag", "collection", "document", "number", "portal"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = kwargs.get("request")
        if request is None:
            request = self.view.request
        self.request = request

    def filter_queryset(self, queryset):
        required_unlisted_filters = {"document", "collection"}
        filter_present = any(
            v
            for k, v in self.form.cleaned_data.items()
            if k in required_unlisted_filters
        )
        if not filter_present:
            queryset = queryset.filter(document__listed=True)
        return super().filter_queryset(queryset)

    def filter_tag(self, qs, name, value):
        return qs.filter(document__tags=value)

    def filter_collection(self, qs, name, collection):
        if not collection.can_read(self.request):
            return qs.none()
        qs = qs.filter(document__in=collection.documents.all())
        qs = self.apply_data_filters(qs, collection.settings.get("filters", []))
        return qs

    def filter_directory(self, qs, name, directory):
        if NULL_VALUE == directory:
            return qs.filter(
                document__filingcabinet_collectiondocument__directory__isnull=True
            )
        if not directory.collection.can_read(self.request):
            return qs.none()
        return qs.filter(
            document__filingcabinet_collectiondocument__directory=directory
        ).order_by("document__filingcabinet_collectiondocument__order")

    def filter_document(self, qs, name, value):
        if not value.can_read(self.request):
            return qs.none()
        return qs.filter(document=value)

    def filter_portal(self, qs, name, portal):
        qs = qs.filter(document__portal=portal)
        qs = self.apply_data_filters(qs, portal.settings.get("filters", []))
        return qs

    def filter_number(self, qs, name, value):
        return qs.filter(number=value)

    def apply_data_filters(self, qs, filters):
        for filt in filters:
            if not filt["key"].startswith("data."):
                continue
            val = self.request.GET.get(filt["key"])
            if not val:
                continue
            data_type = filt.get("datatype")
            if data_type:
                try:
                    if data_type == "int":
                        val = int(val)
                except ValueError:
                    continue
            filt_key = "document__{}".format(filt["key"].replace(".", "__"))
            qs = qs.filter(**{filt_key: val})
        return qs

    def filter_created_at(self, qs, name, value):
        range_kwargs = {}
        if value.start is not None:
            range_kwargs["gte"] = value.start
        if value.stop is not None:
            range_kwargs["lte"] = value.stop

        for comp, val in range_kwargs.items():
            qs = qs.filter(
                Q(
                    **{
                        "document__published_at__isnull": False,
                        "document__published_at__{}".format(comp): val,
                    }
                )
                | Q(
                    **{
                        "document__published_at__isnull": True,
                        "document__created_at__{}".format(comp): val,
                    }
                )
            )
        return qs
