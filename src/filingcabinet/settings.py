from django.conf import settings

FILINGCABINET_DOCUMENT_MODEL = getattr(
    settings, "FILINGCABINET_DOCUMENT_MODEL", "filingcabinet.Document"
)

FILINGCABINET_DOCUMENTCOLLECTION_MODEL = getattr(
    settings,
    "FILINGCABINET_DOCUMENTCOLLECTION_MODEL",
    "filingcabinet.DocumentCollection",
)

TESSERACT_DATA_PATH = getattr(
    settings, "TESSERACT_DATA_PATH", "/usr/local/share/tessdata"
)
FILINGCABINET_ENABLE_WEBP = getattr(settings, "FILINGCABINET_ENABLE_WEBP", False)
FILINGCABINET_MEDIA_PRIVATE_INTERNAL = getattr(
    settings, "FILINGCABINET_MEDIA_PRIVATE_INTERNAL", "/protected/"
)

FILINGCABINET_PAGE_PROCESSING_TIMEOUT = getattr(
    settings,
    "FILINGCABINET_PAGE_PROCESSING_TIMEOUT",
    4 * 60,  # 4 minutes
)
