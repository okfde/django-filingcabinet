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
