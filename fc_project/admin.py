from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from fcdocs_annotate.annotation.admin import predict_feature

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


def try_rgegister(model, model_admin):
    try:
        admin.site.register(model, model_admin)
    except AlreadyRegistered:
        pass


try_rgegister(Document, DocumentBaseAdmin)
try_rgegister(Page, PageAdmin)
try_rgegister(PageAnnotation, PageAnnotationAdmin)
try_rgegister(DocumentCollection, DocumentCollectionBaseAdmin)
try_rgegister(CollectionDocument, CollectionDocumentBaseAdmin)
try_rgegister(DocumentPortal, DocumentPortalAdmin)
try_rgegister(CollectionDirectory, CollectionDirectoryAdmin)

DocumentBaseAdmin.predict_feature = predict_feature
DocumentBaseAdmin.actions += ["predict_feature"]
