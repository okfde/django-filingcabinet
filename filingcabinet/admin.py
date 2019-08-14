from django.contrib import admin
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .models import Page
from .tasks import process_document


class PageInline(admin.StackedInline):
    model = Page
    raw_id_fields = ('document',)


class DocumentBaseAdmin(admin.ModelAdmin):
    inlines = [PageInline]
    save_on_top = True
    search_fields = ('title',)
    date_hierarchy = 'created_at'
    list_display = ('title', 'created_at', 'num_pages', 'public')
    raw_id_fields = ('user',)
    readonly_fields = ('uid',)
    prepopulated_fields = {'slug': ('title',)}
    actions = ('reprocess_document',)

    def get_inline_instances(self, request, obj=None):
        ''' Only show inline for docs with fewer than 31 pages'''
        if obj.num_pages and obj.num_pages <= 30:
            return super().get_inline_instances(request, obj=obj)
        return []

    def save_model(self, request, doc, form, change):
        doc.updated_at = timezone.now()
        super(DocumentBaseAdmin, self).save_model(
            request, doc, form, change)
        if not change:
            process_document.delay(doc.pk)

    def reprocess_document(self, request, queryset):
        for instance in queryset:
            process_document.delay(instance.pk)
        self.message_user(request, _("Started reprocessing documents."))
    reprocess_document.short_description = _("Reprocess document")


class PageAdmin(admin.ModelAdmin):
    raw_id_fields = ('document',)
    search_fields = ('document__title',)
    list_filter = ('number',)
    list_display = ('show_title', 'number')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('document')
        return qs

    def show_title(self, obj):
        return obj.document.title


class PageAnnotationAdmin(admin.ModelAdmin):
    raw_id_fields = ('user', 'page',)


# Register them yourself
# admin.site.register(Document, DocumentAdmin)
# admin.site.register(Page)
