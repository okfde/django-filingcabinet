from collections import defaultdict

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import PermissionDenied
from django.db.models import Case, Count, F, FloatField, JSONField, Q, Sum, When
from django.db.models.functions import Cast
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_json_widget.widgets import JSONEditorWidget
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from . import get_document_model
from .admin_utils import NullFilter
from .models import CollectionDirectory, Page


class DocumentPortalAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title",)
    date_hierarchy = "created_at"
    list_display = (
        "title",
        "created_at",
        "public",
        "get_document_count",
        "processed_documents_percentage",
        "get_pages_count",
    )
    list_filter = ("public",)
    formfield_overrides = {
        JSONField: {
            "widget": JSONEditorWidget(
                # TODO: JS does not work with CSP
                # options={'schema': SETTINGS_SCHEMA}
            )
        },
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            document_count=Count("document"),
            ready_document_count=Count(
                "document", filter=Q(document__pending=False, document__num_pages__gt=0)
            ),
            pages_count=Sum("document__num_pages"),
        )
        return qs

    def get_document_count(self, obj):
        return obj.document_count

    get_document_count.admin_order_field = "document_count"
    get_document_count.short_description = _("Documents")

    def processed_documents_percentage(self, obj):
        if not obj.document_count:
            return "-"
        return "{:.2f}%".format(obj.ready_document_count / obj.document_count * 100)

    processed_documents_percentage.admin_order_field = "ready_document_count"
    processed_documents_percentage.short_description = _("Processed")

    @admin.display(description=_("Pages"))
    def get_pages_count(self, obj):
        return obj.pages_count


class PageInline(admin.StackedInline):
    model = Page
    raw_id_fields = ("document",)


class HasTablesFilter(NullFilter):
    title = _("has detected tables")
    parameter_name = "properties___tables__0"


class DocumentChangeList(ChangeList):
    def get_results(self, *args, **kwargs):
        super().get_results(*args, **kwargs)
        self.result_list = self.result_list.annotate(
            ready_page_count=Count("pages", filter=Q(pages__pending=False)),
        )


class DocumentBaseAdmin(admin.ModelAdmin):
    inlines = [PageInline]
    save_on_top = True
    search_fields = ("title",)
    date_hierarchy = "created_at"
    list_display = (
        "get_title",
        "created_at",
        "public",
        "listed",
        "num_pages",
        "pending",
        "processed_pages_percentage",
    )
    list_filter = (
        "pending",
        "public",
        "listed",
        "allow_annotation",
        "portal",
        HasTablesFilter,
        "created_at",
        "published_at",
    )
    raw_id_fields = ("user",)
    readonly_fields = ("uid", "public", "pending", "content_hash")
    prepopulated_fields = {"slug": ("title",)}
    formfield_overrides = {
        JSONField: {"widget": JSONEditorWidget},
    }
    actions = [
        "process_document",
        "reprocess_document",
        "fix_document_paths",
        "publish_documents",
        "unpublish_documents",
        "mark_unlisted",
        "mark_listed",
        "detect_tables",
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "upload/",
                self.admin_site.admin_view(self.upload_documents),
                name="filingcabinet-document-upload",
            ),
        ]
        return custom_urls + urls

    def get_title(self, obj):
        return obj.title or "<%s>" % obj.pk

    def get_changelist(self, request):
        return DocumentChangeList

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            ready_page_count=Count("pages", filter=Q(pages__pending=False)),
            processed_pages_percentage=Case(
                When(num_pages=0, then=0),
                default=(F("ready_page_count") / Cast(F("num_pages"), FloatField()))
                * 100.0,
                output_field=FloatField(),
            ),
        )

    def processed_pages_percentage(self, obj):
        return "{:.2f}%".format(obj.processed_pages_percentage)

    processed_pages_percentage.admin_order_field = "processed_pages_percentage"
    processed_pages_percentage.short_description = _("Processed")

    def get_inline_instances(self, request, obj=None):
        """Only show inline for docs with fewer than 31 pages"""
        if obj is not None and obj.num_pages and obj.num_pages <= 30:
            return super().get_inline_instances(request, obj=obj)
        return []

    def save_model(self, request, doc, form, change):
        doc.updated_at = timezone.now()
        super().save_model(request, doc, form, change)
        if not change:
            doc.process_document()

    def upload_documents(self, request):
        from .services import create_documents_from_files

        if not request.method == "POST":
            raise PermissionDenied
        if not self.has_change_permission(request):
            raise PermissionDenied

        pdf_files = request.FILES.getlist("file")
        create_documents_from_files(request.user, pdf_files)

        Document = get_document_model()

        return redirect(
            reverse(
                "admin:{}_{}_changelist".format(
                    Document._meta.app_label, Document._meta.model_name
                )
            )
        )

    def process_document(self, request, queryset):
        for instance in queryset:
            instance.process_document(reprocess=False)
        self.message_user(request, _("Started processing documents."))

    process_document.short_description = _("Process documents")

    def reprocess_document(self, request, queryset):
        for instance in queryset:
            instance.process_document(reprocess=True)
        self.message_user(request, _("Started reprocessing documents."))

    reprocess_document.short_description = _("Reprocess documents")

    def fix_document_paths(self, request, queryset):
        from .tasks import files_moved_task

        for instance in queryset:
            files_moved_task.delay(instance.id)

        self.message_user(request, _("Fixing document paths..."))

    fix_document_paths.short_description = _("Fix document paths")

    def publish_documents(self, request, queryset, public=True, message=None):
        from .tasks import publish_document

        if message is None:
            message = _("Publishing {} documents...")

        count = 0
        for instance in queryset:
            if not instance.pending:
                publish_document.delay(instance.pk, public=public)
                count += 1
        if count:
            self.message_user(request, message.format(count))
        else:
            self.message_user(
                request, _("Please select only non-pending documents for publishing.")
            )

    publish_documents.short_description = _("Publish documents")

    def unpublish_documents(self, request, queryset):
        return self.publish_documents(
            request, queryset, public=False, message=_("Unpublishing {} documents...")
        )

    unpublish_documents.short_description = _("Unpublish documents")

    def mark_listed(self, request, queryset):
        queryset.update(listed=True)

    mark_listed.short_description = _("Mark as listed")

    def mark_unlisted(self, request, queryset):
        queryset.update(listed=False)

    mark_unlisted.short_description = _("Mark as unlisted")

    def detect_tables(self, request, queryset):
        from .tasks import detect_tables_document_task

        for doc in queryset:
            detect_tables_document_task.delay(doc.pk)
        self.message_user(request, _("Detecting tables tasks started..."))

    detect_tables.short_description = _("Detect tables")


class PageAdmin(admin.ModelAdmin):
    raw_id_fields = ("document",)
    search_fields = ("document__title",)
    list_filter = (
        "pending",
        "corrected",
        "number",
    )
    list_display = ("show_title", "number", "pending", "corrected")

    actions = ["set_pending", "rotate_90", "rotate_180", "rotate_270"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("document")
        return qs

    def show_title(self, obj):
        return obj.document.title

    @admin.action(description=_("Set to pending"))
    def set_pending(self, request, queryset):
        queryset.update(pending=True)

    @admin.action(description=_("Rotate 90 degrees clockwise"))
    def rotate_90(self, request, queryset):
        self._rotate(request, queryset, 90)

    @admin.action(description=_("Rotate 180 degrees"))
    def rotate_180(self, request, queryset):
        self._rotate(request, queryset, 180)

    @admin.action(description=_("Rotate 90 degrees counter-clockwise"))
    def rotate_270(self, request, queryset):
        self._rotate(request, queryset, 270)

    def _rotate(self, request, queryset, angle):
        from .tasks import rotate_page_task

        docs = defaultdict(list)

        for page in queryset:
            docs[page.document_id].append(page.number)

        for doc_id, page_numbers in docs.items():
            rotate_page_task.delay(doc_id, page_numbers, angle)

        self.message_user(request, _("Rotating pages tasks started..."))


class PageAnnotationAdmin(admin.ModelAdmin):
    raw_id_fields = (
        "user",
        "page",
    )
    date_hierarchy = "timestamp"
    list_display = ("page", "user", "title", "timestamp")
    list_filter = ["page__number"]
    save_on_top = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("user", "page", "page__document")
        return qs


class CollectionDirectoryAdmin(TreeAdmin):
    form = movenodeform_factory(CollectionDirectory)
    raw_id_fields = (
        "user",
        "collection",
    )
    list_display = (
        "name",
        "collection",
        "created_at",
        "updated_at",
    )
    search_fields = ("name",)


class DocumentCollectionBaseAdmin(admin.ModelAdmin):
    raw_id_fields = (
        "user",
        "documents",
    )
    save_on_top = True
    search_fields = ("title",)
    date_hierarchy = "created_at"
    list_display = (
        "title",
        "created_at",
        "public",
        "listed",
        "user",
        "get_document_count",
        "processed_documents_percentage",
    )
    prepopulated_fields = {"slug": ("title",)}
    formfield_overrides = {
        JSONField: {
            "widget": JSONEditorWidget(
                # TODO: JS does not work with CSP
                # options={'schema': SETTINGS_SCHEMA}
            )
        },
    }
    readonly_fields = ("uid", "created_at")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            document_count=Count("documents"),
            ready_document_count=Count("documents", filter=Q(documents__pending=False)),
        )
        return qs

    def get_document_count(self, obj):
        return obj.document_count

    get_document_count.admin_order_field = "document_count"
    get_document_count.short_description = _("Documents")

    def processed_documents_percentage(self, obj):
        if not obj.document_count:
            return "-"
        return "{:.2f}%".format(obj.ready_document_count / obj.document_count * 100)

    processed_documents_percentage.admin_order_field = "ready_document_count"
    processed_documents_percentage.short_description = _("Processed")

    def get_inline_instances(self, request, obj=None):
        """Only show inline for docs with fewer than 31 pages"""
        if obj is not None:
            doc_count = obj.documents.count()
            if doc_count < 31:
                return super().get_inline_instances(request, obj=obj)
        return []


class CollectionDocumentBaseAdmin(admin.ModelAdmin):
    list_display = ("document", "collection", "order", "directory")
    raw_id_fields = ("document", "collection", "directory")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("document", "collection")
        return qs


# Register them yourself
# admin.site.register(Document, DocumentAdmin)
# admin.site.register(Page)
