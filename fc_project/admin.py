from django.contrib import admin

from filingcabinet import get_document_model, get_documentcollection_model
from filingcabinet.admin import (
    CollectionDirectoryAdmin,
    CollectionDocumentBaseAdmin,
    DocumentBaseAdmin,
    DocumentCollectionBaseAdmin,
    DocumentPortalAdmin,
    PageAdmin,
    PageAnnotationAdmin,
)
from filingcabinet.models import (
    CollectionDirectory,
    CollectionDocument,
    DocumentPortal,
    Page,
    PageAnnotation,
)

Document = get_document_model()
DocumentCollection = get_documentcollection_model()

admin.site.register(Document, DocumentBaseAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(PageAnnotation, PageAnnotationAdmin)
admin.site.register(DocumentCollection, DocumentCollectionBaseAdmin)
admin.site.register(CollectionDocument, CollectionDocumentBaseAdmin)
admin.site.register(DocumentPortal, DocumentPortalAdmin)
admin.site.register(CollectionDirectory, CollectionDirectoryAdmin)
