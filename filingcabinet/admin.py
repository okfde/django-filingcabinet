from django.contrib import admin
from django.db.models import Q, Count, JSONField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from mptt.admin import MPTTModelAdmin
from django_json_widget.widgets import JSONEditorWidget

from .models import Page
from .admin_utils import NullFilter


class DocumentPortalAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)
    date_hierarchy = 'created_at'
    list_display = ('title', 'created_at', 'public')
    list_filter = ('public',)
    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget(
            # TODO: JS does not work with CSP
            # options={'schema': SETTINGS_SCHEMA}
        )},
    }


class PageInline(admin.StackedInline):
    model = Page
    raw_id_fields = ('document',)


class HasTablesFilter(NullFilter):
    title = _('has detected tables')
    parameter_name = 'properties___tables__0'


class DocumentBaseAdmin(admin.ModelAdmin):
    inlines = [PageInline]
    save_on_top = True
    search_fields = ('title',)
    date_hierarchy = 'created_at'
    list_display = (
        'title', 'created_at', 'public', 'listed', 'num_pages', 'pending',
        'processed_pages_percentage'
    )
    list_filter = (
        'pending', 'public', 'allow_annotation', 'portal',
        HasTablesFilter
    )
    raw_id_fields = ('user',)
    readonly_fields = (
        'uid', 'public', 'pending',
        'content_hash'
    )
    prepopulated_fields = {'slug': ('title',)}
    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget},
    }
    actions = [
        'process_document', 'reprocess_document', 'fix_document_paths',
        'publish_documents', 'unpublish_documents',
        'mark_unlisted', 'mark_listed', 'detect_tables'
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            ready_page_count=Count('pages', filter=Q(pages__pending=False)),
        )
        return qs

    def processed_pages_percentage(self, obj):
        if not obj.num_pages:
            return '-'
        return '{:.2f}%'.format(obj.ready_page_count / obj.num_pages * 100)
    processed_pages_percentage.admin_order_field = 'ready_page_count'
    processed_pages_percentage.short_description = _('Processed')

    def get_inline_instances(self, request, obj=None):
        ''' Only show inline for docs with fewer than 31 pages'''
        if obj is not None and obj.num_pages and obj.num_pages <= 30:
            return super().get_inline_instances(request, obj=obj)
        return []

    def save_model(self, request, doc, form, change):
        doc.updated_at = timezone.now()
        super().save_model(request, doc, form, change)
        if not change:
            doc.process_document()

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

    def publish_documents(self, request, queryset, public=True,
                          message=_("Publishing {} documents...")):
        from .tasks import publish_document

        count = 0
        for instance in queryset:
            if not instance.pending:
                publish_document.delay(instance.pk, public=public)
                count += 1
        if count:
            self.message_user(
                request,
                message.format(count)
            )
        else:
            self.message_user(
                request,
                _("Please select only non-pending documents for publishing.")
            )
    publish_documents.short_description = _("Publish documents")

    def unpublish_documents(self, request, queryset):
        return self.publish_documents(
            request, queryset, public=False,
            message=_("Unpublishing {} documents...")
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
        self.message_user(
            request,
            _("Detecting tables tasks started...")
        )
    detect_tables.short_description = _("Detect tables")


class PageAdmin(admin.ModelAdmin):
    raw_id_fields = ('document',)
    search_fields = ('document__title',)
    list_filter = ('pending', 'corrected', 'number',)
    list_display = ('show_title', 'number', 'pending', 'corrected')

    actions = ['set_pending']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('document')
        return qs

    def show_title(self, obj):
        return obj.document.title

    def set_pending(self, request, queryset):
        queryset.update(pending=True)
    set_pending.short_description = _('Set to pending')


class PageAnnotationAdmin(admin.ModelAdmin):
    raw_id_fields = ('user', 'page',)
    date_hierarchy = 'timestamp'
    list_display = ('page', 'user', 'title', 'timestamp')
    list_filter = ['page__number']
    save_on_top = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('user', 'page', 'page__document')
        return qs


class CollectionDirectoryAdmin(MPTTModelAdmin):
    raw_id_fields = ('user', 'collection', 'parent')
    list_display = ('name', 'collection', 'created_at', 'updated_at')


class DocumentCollectionBaseAdmin(admin.ModelAdmin):
    raw_id_fields = ('user', 'documents',)
    save_on_top = True
    search_fields = ('title',)
    date_hierarchy = 'created_at'
    list_display = (
        'title', 'created_at', 'public', 'listed', 'user',
        'get_document_count',
        'processed_documents_percentage'
    )
    prepopulated_fields = {'slug': ('title',)}
    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget(
            # TODO: JS does not work with CSP
            # options={'schema': SETTINGS_SCHEMA}
        )},
    }
    readonly_fields = (
        'uid', 'created_at'
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            document_count=Count('documents'),
            ready_document_count=Count(
                'documents',
                filter=Q(documents__pending=False)
            ),
        )
        return qs

    def get_document_count(self, obj):
        return obj.document_count
    get_document_count.admin_order_field = 'document_count'
    get_document_count.short_description = _('Documents')

    def processed_documents_percentage(self, obj):
        if not obj.document_count:
            return '-'
        return '{:.2f}%'.format(
            obj.ready_document_count / obj.document_count * 100
        )
    processed_documents_percentage.admin_order_field = 'ready_document_count'
    processed_documents_percentage.short_description = _('Processed')

    def get_inline_instances(self, request, obj=None):
        ''' Only show inline for docs with fewer than 31 pages'''
        if obj is not None:
            doc_count = obj.documents.count()
            if doc_count < 31:
                return super().get_inline_instances(request, obj=obj)
        return []


class CollectionDocumentBaseAdmin(admin.ModelAdmin):
    list_display = ('document', 'collection', 'order')
    raw_id_fields = ('document', 'collection', 'directory')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('document', 'collection')
        return qs


# Register them yourself
# admin.site.register(Document, DocumentAdmin)
# admin.site.register(Page)
