import functools
import os
import shutil
import uuid

from django.conf.locale import LANG_INFO
from django.utils import timezone
from django.db import models
from django.core.files.base import File
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from taggit.models import TaggedItemBase
from taggit.managers import TaggableManager

from .storage import OverwriteStorage
from .settings import (
    FILINGCABINET_DOCUMENT_MODEL,
    FILINGCABINET_DOCUMENTCOLLECTION_MODEL
)


class DocumentManager(models.Manager):
    pass


def get_document_file_path(instance, filename):
    # UUID field is already filled
    hex_name = instance.uid.hex
    hex_name_02 = hex_name[:2]
    hex_name_24 = hex_name[2:4]
    hex_name_46 = hex_name[4:6]
    prefix = settings.FILINGCABINET_MEDIA_PUBLIC_PREFIX
    if not instance.public:
        prefix = settings.FILINGCABINET_MEDIA_PRIVATE_PREFIX
    return os.path.join(prefix, hex_name_02, hex_name_24,
                        hex_name_46, hex_name, filename)


def get_document_path(instance, filename):
    name, ext = os.path.splitext(filename)
    slug = slugify(name)
    return get_document_file_path(instance, slug + ext)


def get_page_image_filename(prefix='page', page='{page}', size='{size}',
                            filetype='png'):
    return '{prefix}-p{page}-{size}.{filetype}'.format(
        prefix=prefix,
        size=size,
        page=page,
        filetype=filetype
    )


class TaggedDocument(TaggedItemBase):
    content_object = models.ForeignKey(
        FILINGCABINET_DOCUMENT_MODEL,
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _('Document Tag')
        verbose_name_plural = _('Document Tags')


class AbstractDocument(models.Model):
    LANGUAGE_CHOICES = [(k, LANG_INFO[k]['name']) for k in LANG_INFO
                        if 'name' in LANG_INFO[k]]

    uid = models.UUIDField(default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=500, default='', blank=True)
    slug = models.SlugField(max_length=250, blank=True)
    description = models.TextField(default='', blank=True)

    pdf_file = models.FileField(
        max_length=255,
        storage=OverwriteStorage(),
        upload_to=get_document_path, blank=True)
    file_size = models.BigIntegerField(null=True)
    pending = models.BooleanField(default=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s',
        verbose_name=_("User")
    )

    created_at = models.DateTimeField(default=timezone.now, null=True)
    updated_at = models.DateTimeField(default=timezone.now, null=True)

    num_pages = models.PositiveIntegerField(default=0)

    language = models.CharField(max_length=10, blank=True,
                                default=settings.LANGUAGE_CODE,
                                choices=settings.LANGUAGES)

    public = models.BooleanField(default=False)
    tags = TaggableManager(
        through=TaggedDocument, blank=True,
        related_name='+'
    )

    objects = DocumentManager()

    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_public = self.public

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        public_changed = self._old_public != self.public
        if public_changed and self.pk and self.pdf_file:
            self._move_file()
            self._old_public = self.public
        super().save(*args, **kwargs)
    save.alters_data = True

    def get_absolute_url(self):
        if self.slug:
            return reverse('document-detail', kwargs={
                'pk': self.pk,
                'slug': self.slug
            })
        return reverse('document-detail_short', kwargs={
            'pk': self.pk
        })

    def get_absolute_domain_url(self):
        return settings.SITE_URL + self.get_absolute_url()

    @property
    def has_original(self):
        if not hasattr(self, 'original_id'):
            return False
        if not self.original_id:
            return False
        return True

    def get_progress(self):
        if self.num_pages:
            pages_done = self.page_set.filter(pending=False).count()
            return int(pages_done / self.num_pages * 100)
        return None

    def get_file_path(self):
        if self.pdf_file:
            return self.pdf_file.path
        if self.has_original:
            return self.original.get_file_path()
        return ''

    def get_document_filename(self):
        return self.get_file_path().rsplit('/', 1)[1]

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
        return ''

    def get_file_url(self, filename=None):
        if filename is None:
            return self.get_document_file_url()
        if self.public:
            return settings.MEDIA_URL + self.get_file_name(filename=filename)
        uid = self.uid.hex
        return reverse(
            'filingcabinet-auth_document',
            kwargs={
                'u1': uid[0:2],
                'u2': uid[2:4],
                'u3': uid[4:6],
                'uuid': uid,
                'filename': filename
            })

    def get_crossdomain_auth(self, filename=None):
        from .auth import DocumentCrossDomainMediaAuth

        if filename is None:
            filename = self.get_document_filename()

        return DocumentCrossDomainMediaAuth({
            'object': self,
            'filename': filename
        })

    def get_authorized_file_url(self, filename=None):
        if self.public:
            return self.get_file_url(filename=filename)
        return self.get_crossdomain_auth(filename=filename).get_full_media_url(
            authorized=True
        )

    def _move_file(self):
        """
        Move the file from src to dst.
        This uses direct filesystem operations for efficiency
        and not replicating/copying all thumbnails
        """
        if not self.pdf_file:
            # Original data holder is responsible for secure serving
            return
        src_file_dir = os.path.dirname(self.pdf_file.path)
        dst_file_name = get_document_path(self, self.get_document_filename())
        dst_file_dir = os.path.dirname(os.path.join(
            settings.MEDIA_ROOT, dst_file_name
        ))
        self.pdf_file = dst_file_name
        try:
            if src_file_dir != dst_file_dir:
                shutil.rmtree(dst_file_dir, ignore_errors=True)
            shutil.move(src_file_dir, dst_file_dir)
        except IOError:
            pass

    def get_page_template(self):
        return self.get_authorized_file_url(filename=get_page_image_filename())

    def get_cover_image(self):
        return self.get_authorized_file_url(filename=get_page_image_filename(
            page=1, size='small'
        ))

    def get_serializer_class(self, detail=False):
        from .api_views import DocumentSerializer, DocumentDetailSerializer

        if detail:
            return DocumentDetailSerializer
        return DocumentSerializer

    def get_writeable_file(self):
        if not self.pdf_file:
            with open(self.get_file_path(), 'rb') as f:
                self.pdf_file.save('document.pdf', File(f))
        return self.pdf_file.path

    def process_document(self, reprocess=True):
        from .tasks import process_document_task

        self.pending = True
        self.save()

        if reprocess:
            Page.objects.filter(document=self).update(pending=True)

        process_document_task.delay(self.id)


class Document(AbstractDocument):
    class Meta(AbstractDocument.Meta):
        swappable = 'FILINGCABINET_DOCUMENT_MODEL'


def get_page_filename(instance, filename, size=''):
    doc_path = get_document_path(instance.document, 'page.png')
    path, ext = os.path.splitext(doc_path)
    return get_page_image_filename(
        prefix=path, page=instance.number, size=size
    )


class Page(models.Model):
    SIZES = (
        # Wide in px
        ('large', 1000),
        ('normal', 700),
        ('small', 180)
    )

    UPLOAD_FUNCS = {
        size[0]: functools.partial(get_page_filename, size=size[0])
        for size in SIZES
    }

    document = models.ForeignKey(
        FILINGCABINET_DOCUMENT_MODEL,
        on_delete=models.CASCADE
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
        upload_to=functools.partial(get_page_filename, size='original'))
    image_large = models.ImageField(
        max_length=255,
        storage=OverwriteStorage(),
        upload_to=UPLOAD_FUNCS['large'])
    image_normal = models.ImageField(
        max_length=255,
        storage=OverwriteStorage(),
        upload_to=UPLOAD_FUNCS['normal'])
    image_small = models.ImageField(
        max_length=255,
        storage=OverwriteStorage(),
        upload_to=UPLOAD_FUNCS['small'])

    class Meta:
        unique_together = ('document', 'number')
        ordering = ('number',)

    def __str__(self):
        return '%s - %s' % (self.document, self.number)

    def get_absolute_url(self):
        return '{}#page-{}'.format(
            self.document.get_absolute_url(),
            self.number
        )

    def get_image_url(self, size='{size}'):
        templ = self.document.get_page_image_url_template()
        return settings.MEDIA_URL + templ.format(
            page=self.number, size=size
        )

    def dim_ratio_percent(self):
        if self.width and self.height:
            return str(self.height / self.width * 100)
        return str(70)


def get_page_annotation_filename(instance, filename):
    # UUID field is already filled
    filename = instance.page.image.name
    base_name, _ = os.path.splitext(filename)
    return '%s-annotation-%s.png' % (
        base_name,
        instance.pk
    )


class PageAnnotation(models.Model):
    page = models.ForeignKey(
        Page, null=True, on_delete=models.SET_NULL
    )

    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True,
        related_name='%(app_label)s_%(class)s',
        on_delete=models.SET_NULL,
        verbose_name=_("User")
    )

    top = models.IntegerField(null=True, blank=True)
    left = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    highlight = models.TextField(blank=True)
    image = models.ImageField(upload_to=get_page_annotation_filename,
                              storage=OverwriteStorage(),
                              max_length=255, blank=True)

    def __str__(self):
        return '%s (%s)' % (self.title, self.page)

    def save(self, *args, **kwargs):
        from .services import make_page_annotation

        image_cropped = kwargs.pop('image_cropped', False)
        res = super(PageAnnotation, self).save(*args, **kwargs)
        if not image_cropped and self.valid_rect():
            make_page_annotation(self)
            return self.save(image_cropped=True)
        return res

    def valid_rect(self):
        return (self.left is not None and
                self.top is not None and
                self.width is not None and
                self.height is not None)


class CollectionDocument(models.Model):
    collection = models.ForeignKey(
        FILINGCABINET_DOCUMENTCOLLECTION_MODEL,
        related_name='%(app_label)s_%(class)s',
        on_delete=models.CASCADE
    )
    document = models.ForeignKey(
        FILINGCABINET_DOCUMENT_MODEL,
        related_name='%(app_label)s_%(class)s',
        on_delete=models.CASCADE
    )


class AbstractDocumentCollection(models.Model):
    slug = models.SlugField(max_length=250, blank=True)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    public = models.BooleanField(default=True)

    documents = models.ManyToManyField(
        FILINGCABINET_DOCUMENT_MODEL,
        related_name='%(app_label)s_%(class)s',
        blank=True,
        through=CollectionDocument,
        through_fields=('collection', 'document')
    )

    class Meta:
        abstract = True


class DocumentCollection(AbstractDocumentCollection):
    class Meta(AbstractDocumentCollection.Meta):
        swappable = 'FILINGCABINET_DOCUMENTCOLLECTION_MODEL'
