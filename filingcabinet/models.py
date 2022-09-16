import functools
import os
import shutil
import urllib.parse
import uuid

from django.conf import settings
from django.conf.locale import LANG_INFO
from django.core.files.base import File
from django.db import models
from django.urls import Resolver404, resolve, reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from .settings import (
    FILINGCABINET_DOCUMENT_MODEL,
    FILINGCABINET_DOCUMENTCOLLECTION_MODEL,
)
from .storage import OverwriteStorage
from .utils import get_local_file
from .validators import validate_settings_schema


class DocumentPortal(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250)

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    public = models.BooleanField(default=False)

    settings = models.JSONField(
        blank=True, default=dict, validators=[validate_settings_schema]
    )

    class Meta:
        verbose_name = _("document portal")
        verbose_name_plural = _("document portals")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("filingcabinet:document-portal", kwargs={"slug": self.slug})

    def get_serializer_class(self):
        from .api_serializers import DocumentPortalSerializer

        return DocumentPortalSerializer

    @property
    def documents(self):
        from . import get_document_model

        return get_document_model().objects.filter(portal=self)

    @property
    def ordered_documents(self):
        from . import get_document_model

        return get_document_model().objects.filter(portal=self)

    def can_read_unlisted(self, request):
        return True

    def can_read(self, request):
        if request.user.is_superuser:
            return True
        return self.public

    def can_write(self, request):
        return False


class AuthQuerysetMixin:
    def get_authenticated_queryset(self, request):
        qs = self.get_queryset()
        cond = models.Q(public=True)
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return qs
            cond |= models.Q(user=request.user)
        return qs.filter(cond)


class OEmbedMixin:
    def get_public_via_url(self, url):
        result = urllib.parse.urlparse(url)
        try:
            match = resolve(result.path)
        except Resolver404:
            return None
        pk = match.kwargs.get("pk")
        if pk is None:
            return None
        try:
            # either listed or known by slug
            return (
                self.get_queryset()
                .filter(
                    models.Q(public=True, listed=True)
                    | models.Q(public=True, slug=match.kwargs.get("slug", ""))
                )
                .get(id=pk)
            )
        except models.Model.DoesNotExist:
            return None


class DocumentManager(OEmbedMixin, AuthQuerysetMixin, models.Manager):
    pass


def get_document_file_path(instance, filename, public=None):
    # UUID field is already filled
    hex_name = instance.uid.hex
    hex_name_02 = hex_name[:2]
    hex_name_24 = hex_name[2:4]
    hex_name_46 = hex_name[4:6]
    prefix = settings.FILINGCABINET_MEDIA_PUBLIC_PREFIX
    if public is False or not instance.public:
        prefix = settings.FILINGCABINET_MEDIA_PRIVATE_PREFIX
    return os.path.join(
        prefix, hex_name_02, hex_name_24, hex_name_46, hex_name, filename
    )


def get_document_path(instance, filename):
    name, ext = os.path.splitext(filename)
    slug = slugify(name)[:80]
    return get_document_file_path(instance, slug + ext)


def get_page_image_filename(
    prefix="page", page="{page}", size="{size}", filetype="png"
):
    return "{prefix}-p{page}-{size}.{filetype}".format(
        prefix=prefix, size=size, page=page, filetype=filetype
    )


class TaggedDocument(TaggedItemBase):
    content_object = models.ForeignKey(
        FILINGCABINET_DOCUMENT_MODEL, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("Document Tag")
        verbose_name_plural = _("Document Tags")


class AbstractDocument(models.Model):
    LANGUAGE_CHOICES = [
        (k, LANG_INFO[k]["name"]) for k in LANG_INFO if "name" in LANG_INFO[k]
    ]

    uid = models.UUIDField(default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=500, default="", blank=True)
    slug = models.SlugField(max_length=250, blank=True)
    description = models.TextField(default="", blank=True)

    pdf_file = models.FileField(
        max_length=255,
        storage=OverwriteStorage(),
        upload_to=get_document_path,
        blank=True,
    )
    file_size = models.BigIntegerField(null=True, blank=True)
    pending = models.BooleanField(default=False)

    content_hash = models.CharField(
        null=True, blank=True, max_length=40, editable=False
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s",
        verbose_name=_("User"),
    )

    created_at = models.DateTimeField(default=timezone.now, null=True)
    updated_at = models.DateTimeField(default=timezone.now, null=True)
    published_at = models.DateTimeField(default=None, null=True, blank=True)

    num_pages = models.PositiveIntegerField(default=0)

    language = models.CharField(
        max_length=10,
        blank=True,
        default=settings.LANGUAGE_CODE,
        choices=settings.LANGUAGES,
    )

    public = models.BooleanField(default=False)
    listed = models.BooleanField(default=True)
    allow_annotation = models.BooleanField(default=False)
    properties = models.JSONField(blank=True, default=dict)
    data = models.JSONField(blank=True, default=dict)
    outline = models.TextField(blank=True)

    tags = TaggableManager(through=TaggedDocument, blank=True, related_name="+")
    portal = models.ForeignKey(
        DocumentPortal, null=True, blank=True, on_delete=models.SET_NULL
    )

    objects = DocumentManager()

    FORMAT_KEY = "_format_{}"

    class Meta:
        verbose_name = _("document")
        verbose_name_plural = _("documents")
        abstract = True
        indexes = [
            models.Index(
                fields=["content_hash"],
                name="fc_document_chash_idx",
                condition=models.Q(content_hash__isnull=False),
            )
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_public = self.public

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if self.slug:
            return reverse(
                "filingcabinet:document-detail",
                kwargs={"pk": self.pk, "slug": self.slug},
            )
        return reverse("filingcabinet:document-detail_short", kwargs={"pk": self.pk})

    def get_absolute_domain_url(self):
        return getattr(settings, "SITE_URL", "") + self.get_absolute_url()

    def get_absolute_domain_embed_url(self):
        path = reverse(
            "filingcabinet:document-detail_embed_short",
            kwargs={
                "pk": self.pk,
            },
        )
        return getattr(settings, "SITE_URL", "") + path

    @property
    def has_original(self):
        if not hasattr(self, "original_id"):
            return False
        if not self.original_id:
            return False
        return True

    @property
    def unlisted(self):
        return not self.listed

    def get_progress(self):
        if self.num_pages:
            pages_done = self.pages.filter(pending=False).count()
            return int(pages_done / self.num_pages * 100)
        return None

    def get_file_path(self):
        if self.pdf_file:
            return self.pdf_file.path
        if self.has_original:
            return self.original.get_file_path()
        return ""

    def get_local_file(self):
        return get_local_file(self.get_file_path())

    def get_document_filename(self):
        return self.get_file_path().rsplit("/", 1)[1]

    def get_file_name(self, filename=None):
        if filename is None:
            filename = self.get_document_filename()
        return get_document_file_path(self, filename)

    def get_document_file_url(self):
        if self.pdf_file:
            if self.public:
                return self.pdf_file.url
            return self.get_file_url(filename=self.get_document_filename())
        if self.has_original:
            return self.original.get_file_url()
        return ""

    def get_file_url(self, filename=None):
        if filename is None:
            return self.get_document_file_url()
        if self.public:
            return settings.MEDIA_URL + self.get_file_name(filename=filename)
        uid = self.uid.hex
        return reverse(
            "filingcabinet-auth_document",
            kwargs={
                "u1": uid[0:2],
                "u2": uid[2:4],
                "u3": uid[4:6],
                "uuid": uid,
                "filename": filename,
            },
        )

    def delete(self, **kwargs):
        # FIXME: this should be storage system agnostic
        res = super().delete(**kwargs)
        dir_path = os.path.dirname(get_document_file_path(self, "foo"))
        shutil.rmtree(dir_path, ignore_errors=True)
        return res

    def _move_file(self):
        """
        Move the file from src to dst.
        This uses direct filesystem operations for efficiency
        and not replicating/copying all thumbnails
        """
        # FIXME: this should be storage system agnostic
        if not self.pending:
            return
        dummy_src_file_name = get_document_file_path(self, "dummy.pdf", not self.public)
        src_file_dir = os.path.dirname(
            os.path.join(settings.MEDIA_ROOT, dummy_src_file_name)
        )

        if self.pdf_file:
            dst_file_name = get_document_path(self, self.get_document_filename())
        else:
            dst_file_name = get_document_file_path(self, "dummy.pdf")
        dst_file_dir = os.path.dirname(os.path.join(settings.MEDIA_ROOT, dst_file_name))
        try:
            src_exists = os.path.exists(src_file_dir)
            if src_file_dir != dst_file_dir and src_exists:
                shutil.rmtree(dst_file_dir, ignore_errors=True)
            shutil.move(src_file_dir, dst_file_dir)
            if self.pdf_file:
                self.pdf_file = dst_file_name
        except IOError:
            pass

    def get_page_template(self, page="{page}", size="{size}", filetype="png"):
        return self.get_file_url(
            filename=get_page_image_filename(page=page, size=size, filetype=filetype)
        )

    def get_cover_image(self, filetype="png"):
        return self.get_file_url(
            filename=get_page_image_filename(page=1, size="small", filetype=filetype)
        )

    def get_full_cover_image(self, filetype="png"):
        return self.get_file_url(
            filename=get_page_image_filename(page=1, size="original", filetype=filetype)
        )

    @classmethod
    def get_serializer_class(cls, detail=False):
        from .api_serializers import DocumentDetailSerializer, DocumentSerializer

        if detail:
            return DocumentDetailSerializer
        return DocumentSerializer

    def can_read_unlisted(self, request):
        if self.public and self.listed:
            return True
        if self.public and not self.listed:
            if request.GET.get("uid") == str(self.uid):
                return True
        return False

    def can_read(self, request):
        if self.can_read_unlisted(request):
            return True
        if request.user.is_superuser:
            return True
        if request.user.is_authenticated:
            return request.user == self.user
        return False

    def can_write(self, request):
        if request.user.is_superuser:
            return True
        if request.user.is_authenticated:
            return request.user == self.user
        return False

    @classmethod
    def get_annotatable(cls, request):
        if request.user.is_superuser:
            return cls.objects.all()
        cond = models.Q(public=True, allow_annotation=True)
        if request.user.is_authenticated:
            cond |= models.Q(user=request.user)
        return cls.objects.filter(cond)

    def get_writeable_file(self):
        if not self.pdf_file:
            with open(self.get_file_path(), "rb") as f:
                self.pdf_file.save("document.pdf", File(f))
        return self.pdf_file.path

    def process_document(self, reprocess=True):
        from .tasks import process_document_task

        if reprocess:
            Page.objects.filter(document=self).update(pending=True)
            webp_marker = self.FORMAT_KEY.format("webp")
            try:
                del self.properties[webp_marker]
            except KeyError:
                pass

        self.pending = True
        self.save()

        process_document_task.delay(self.id)

    def publish_delayed(self):
        from .tasks import publish_document

        publish_document.delay(self.pk, public=True)

    def unpublish_delayed(self):
        from .tasks import publish_document

        publish_document.delay(self.pk, public=False)

    def has_format(self, format):
        format_marker = self.FORMAT_KEY.format(format)
        return self.properties.get(format_marker) is True

    def has_format_webp(self):
        return self.has_format("webp")


class Document(AbstractDocument):
    class Meta(AbstractDocument.Meta):
        swappable = "FILINGCABINET_DOCUMENT_MODEL"


def get_page_filename(instance, filename, size=""):
    doc_path = get_document_path(instance.document, "page.png")
    path, ext = os.path.splitext(doc_path)
    return get_page_image_filename(prefix=path, page=instance.number, size=size)


class Page(models.Model):
    SIZES = (
        # Wide in px
        ("large", 1000),
        ("normal", 700),
        ("small", 180),
    )

    UPLOAD_FUNCS = {
        size[0]: functools.partial(get_page_filename, size=size[0]) for size in SIZES
    }

    document = models.ForeignKey(
        FILINGCABINET_DOCUMENT_MODEL, related_name="pages", on_delete=models.CASCADE
    )
    number = models.IntegerField(default=1)
    pending = models.BooleanField(default=False)

    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)

    content = models.TextField(blank=True)
    corrected = models.BooleanField(default=False)

    image = models.ImageField(
        max_length=255,
        storage=OverwriteStorage(),
        upload_to=functools.partial(get_page_filename, size="original"),
    )
    image_large = models.ImageField(
        max_length=255, storage=OverwriteStorage(), upload_to=UPLOAD_FUNCS["large"]
    )
    image_normal = models.ImageField(
        max_length=255, storage=OverwriteStorage(), upload_to=UPLOAD_FUNCS["normal"]
    )
    image_small = models.ImageField(
        max_length=255, storage=OverwriteStorage(), upload_to=UPLOAD_FUNCS["small"]
    )

    class Meta:
        unique_together = ("document", "number")
        ordering = ("number",)

    def __str__(self):
        return "%s - %s" % (self.document, self.number)

    def get_absolute_url(self):
        return "{}?page={}".format(self.document.get_absolute_url(), self.number)

    def get_image_url(self, size="{size}", filetype="png"):
        return self.document.get_page_template(
            page=self.number, size=size, filetype=filetype
        )

    def get_preview_image_url(self, filetype="png"):
        return self.document.get_page_template(
            page=self.number, size="small", filetype=filetype
        )

    def get_preview_image_url_webp(self):
        return self.get_preview_image_url(filetype="png.webp")

    def get_normal_image_url(self, filetype="png"):
        return self.document.get_page_template(
            page=self.number, size="normal", filetype=filetype
        )

    def get_large_image_url(self, filetype="png"):
        return self.document.get_page_template(
            page=self.number, size="large", filetype=filetype
        )

    def get_original_image_url(self, filetype="png"):
        return self.document.get_page_template(
            page=self.number, size="original", filetype=filetype
        )

    def dim_ratio_percent(self):
        if self.width and self.height:
            return str(self.height / self.width * 100)
        return str(70)

    def get_image_srcset(self, ext=""):
        return (
            "{preview} 180w, {normal} 700w, {large} 1000w, {original} {width}w".format(
                preview=self.get_preview_image_url(filetype="png{}".format(ext)),
                normal=self.get_normal_image_url(filetype="png{}".format(ext)),
                large=self.get_large_image_url(filetype="png{}".format(ext)),
                original=self.get_original_image_url(filetype="png{}".format(ext)),
                width=self.width,
            )
        )

    def get_image_srcset_webp(self):
        return self.get_image_srcset(ext=".webp")


def get_page_annotation_filename(instance, filename):
    # UUID field is already filled
    filename = instance.page.image.name
    base_name, _ = os.path.splitext(filename)
    return "%s-annotation-%s.png" % (base_name, instance.pk)


class PageAnnotation(models.Model):
    page = models.ForeignKey(Page, null=True, on_delete=models.SET_NULL)

    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name="%(app_label)s_%(class)s",
        on_delete=models.SET_NULL,
        verbose_name=_("User"),
    )

    top = models.IntegerField(null=True, blank=True)
    left = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    highlight = models.TextField(blank=True)
    image = models.ImageField(
        upload_to=get_page_annotation_filename,
        storage=OverwriteStorage(),
        max_length=255,
        blank=True,
    )

    class Meta:
        ordering = ("-timestamp",)

    def __str__(self):
        return "%s (%s)" % (self.title, self.page)

    def save(self, *args, **kwargs):
        from .services import make_page_annotation

        image_cropped = kwargs.pop("image_cropped", False)
        res = super().save(*args, **kwargs)
        if not image_cropped and self.valid_rect():
            make_page_annotation(self)
            return self.save(image_cropped=True)
        return res

    def valid_rect(self):
        return (
            self.left is not None
            and self.top is not None
            and self.width is not None
            and self.height is not None
        )


class CollectionDirectory(MPTTModel):
    name = models.CharField(max_length=255)
    collection = models.ForeignKey(
        FILINGCABINET_DOCUMENTCOLLECTION_MODEL, on_delete=models.CASCADE
    )
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    created_at = models.DateTimeField(_("created at"), default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now, null=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s",
        verbose_name=_("User"),
    )

    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta:
        verbose_name = _("Collection directory")
        verbose_name_plural = _("Collection directories")

    def __str__(self):
        return self.name


class CollectionDocument(models.Model):
    collection = models.ForeignKey(
        FILINGCABINET_DOCUMENTCOLLECTION_MODEL,
        related_name="%(app_label)s_%(class)s",
        on_delete=models.CASCADE,
    )
    document = models.ForeignKey(
        FILINGCABINET_DOCUMENT_MODEL,
        related_name="%(app_label)s_%(class)s",
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=0, blank=False, null=False)
    directory = models.ForeignKey(
        CollectionDirectory,
        verbose_name=_("directory"),
        related_name="documents",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["order", "document__title"]
        constraints = [
            models.UniqueConstraint(
                fields=["collection", "document"],
                name="unique_doc_collection_%(app_label)s_%(class)s",
            ),
        ]


class DocumentCollectionManager(OEmbedMixin, AuthQuerysetMixin, models.Manager):
    pass


class AbstractDocumentCollection(models.Model):
    title = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=250, blank=True)
    description = models.TextField(blank=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s",
        verbose_name=_("User"),
    )

    created_at = models.DateTimeField(default=timezone.now, null=True)
    updated_at = models.DateTimeField(default=timezone.now, null=True)
    settings = models.JSONField(
        blank=True, default=dict, validators=[validate_settings_schema]
    )

    public = models.BooleanField(default=True)
    listed = models.BooleanField(default=True)

    documents = models.ManyToManyField(
        FILINGCABINET_DOCUMENT_MODEL,
        related_name="%(app_label)s_%(class)s",
        blank=True,
        through=CollectionDocument,
        through_fields=("collection", "document"),
    )
    portal = models.ForeignKey(
        DocumentPortal, null=True, blank=True, on_delete=models.SET_NULL
    )

    objects = DocumentCollectionManager()

    class Meta:
        verbose_name = _("document collection")
        verbose_name_plural = _("document collections")
        abstract = True

    def __str__(self):
        return self.title

    @property
    def ordered_documents(self):
        if not hasattr(self, "_ordered_documents"):
            self._ordered_documents = self.get_documents()
        return self._ordered_documents

    def get_documents(self, directory=None):
        return (
            self.documents.all()
            .filter(filingcabinet_collectiondocument__directory=directory)
            .order_by("filingcabinet_collectiondocument__order")
        )

    @property
    def root_directories(self):
        if not hasattr(self, "_root_directories"):
            self._root_directories = self.get_directories()
        return self._root_directories

    @property
    def unlisted(self):
        return not self.listed

    def get_directories(self, parent_directory=None):
        return CollectionDirectory.objects.all().filter(
            collection=self, parent=parent_directory
        )

    def get_absolute_url(self):
        if self.slug:
            return reverse(
                "filingcabinet:document-collection",
                kwargs={"pk": self.pk, "slug": self.slug},
            )
        return reverse(
            "filingcabinet:document-collection_short", kwargs={"pk": self.pk}
        )

    def get_absolute_domain_url(self):
        return getattr(settings, "SITE_URL", "") + self.get_absolute_url()

    def get_absolute_domain_embed_url(self):
        path = reverse(
            "filingcabinet:document-collection_embed_short", kwargs={"pk": self.pk}
        )
        return getattr(settings, "SITE_URL", "") + path

    def get_cover_image(self):
        try:
            document = self.ordered_documents[0]
            return document.get_cover_image()
        except IndexError:
            return None

    @classmethod
    def get_serializer_class(cls, detail=False):
        from .api_serializers import DocumentCollectionSerializer

        return DocumentCollectionSerializer

    def can_read_unlisted(self, request):
        if self.public and self.listed:
            return True
        if self.public and not self.listed:
            if request.GET.get("uid") == str(self.uid):
                return True
        return False

    def can_read(self, request):
        if self.can_read_unlisted(request):
            return True
        if request.user.is_superuser:
            return True
        if request.user.is_authenticated:
            return request.user == self.user
        return False

    def can_write(self, request):
        if request.user.is_superuser:
            return True
        if request.user.is_authenticated:
            return request.user == self.user
        return False


class DocumentCollection(AbstractDocumentCollection):
    class Meta(AbstractDocumentCollection.Meta):
        swappable = "FILINGCABINET_DOCUMENTCOLLECTION_MODEL"
