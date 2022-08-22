from datetime import datetime
import os
import json
import copy

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.template import Template, Context
from django.utils.text import Truncator
from django.contrib.postgres.fields import JSONField
from django.utils.safestring import mark_safe

from swim.core.models import (
    ModelBase,
    ModelIsContentType,
    ContentSchemaMember,
)

from swim.core.content import (
        register_atom_type,
        ReferencedAtomType,
    )

from swim.core import modelfields, WithRelated
from swim.core.models import ContentSlot, KeyedType

from swim.media import image
from swim.media.fields import FileField, ImageField, VariantDict, VariantInfoDict

#-------------------------------------------------------------------------------
class Folder(ModelIsContentType):
    name = models.CharField(max_length=255)

    #---------------------------------------------------------------------------
    def __str__(self):
        return self.name

    #---------------------------------------------------------------------------
    def image_count(self):
        return self.images.all().count()

    #---------------------------------------------------------------------------
    def file_count(self):
        return self.files.all().count()

    #---------------------------------------------------------------------------
    class Meta:
        ordering = ['name', 'id']


#-------------------------------------------------------------------------------
def _image_upload(instance, filename):

    # Assumes that images with the same name won't be uploaded at the same second
    # if they do, django will add an underscore to the second one.
    date_str = instance.creationdate.strftime("%y%m%d-%H%M%S")
    return 'content/image/%s/' % (date_str,)

#-------------------------------------------------------------------------------
class ImageBase(ModelIsContentType):
    """Generic image model
    """
    folder = models.ForeignKey(
        Folder,
        blank=True,
        null=True,
        related_name="images",
        on_delete=models.CASCADE,
    )

    image = ImageField(
        max_length=1024,
        upload_to=_image_upload,
        variants=getattr(
            settings,
            'SWIM_MEDIA_IMAGE_VARIANTS',
            {}
        )
    )
    image_basename = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        editable=False,
    )

    title = models.CharField(
        max_length=1024,
        blank=True,
        null=True,
        help_text="""
            This is optional and may appear as a tool tip when hovering over the image.
        """
    )
    alt = models.CharField(
        max_length=1024,
        blank=True,
        null=True,
        help_text="""
            This text should describe the contents of the image. It will be
            used as alternative text in place of the image for situations
            where the image is not available. This includes text only displays
            or displays for the visually impaired. Although this text is not
            required - we strongly recommend its use as search engines will
            reward your page ranking when this text is in place.
        """
    )
    caption = models.CharField(
        max_length=1024,
        blank=True,
        null=True,
        help_text="""
            The image caption is usually displayed beside or on top of
            the actual image used.  It is intended to contain additional
            information about the image that will enhance its viewing.
            It may describe the image as well, but descriptions of the
            content of the image are best placed in the alt above.
        """
    )

    auto_thumbs = {
        "admin-thumb": {'width': 300, 'height': 300},
        "browser-thumb-128": {'width': 128, 'height': 128},
        "browser-thumb-150": {'width': 150, 'height': 150},
        "browser-thumb": {'width': 256, 'height': 256},
    }


    #---------------------------------------------------------------------------
    def admin_thumbnail(self):
        """
        Generates a snippet of HTML for an img tag that refers to the admin thumb.

        Not intended for general use, this is intended for use in the admin.
        """
        if self.image:
            name = 'admin-thumb'
            url = self.image.generate_variant(name, 'thumbnail', **{
                'width': self.auto_thumbs[name]['width'],
                'height': self.auto_thumbs[name]['height'],
            })
            return mark_safe(f'<img src="{url}" alt="{self.alt}" />')
        else:
            return 'No Image'
    admin_thumbnail.short_description = "Image"

    #---------------------------------------------------------------------------
    def browser_thumbnail(self):
        """
        Generates a snippet of HTML for an img tag that refers to the browser thumb.

        Not intended for general use, this is intended for use in the image browser
        for ck_editor.
        """
        if self.image:
            thumbnail_name = 'browser-thumb-150'
            url = self.image.generate_variant(
                    thumbnail_name,
                    'thumbnail',
                    width=self.auto_thumbs[thumbnail_name]['width'],
                    height=self.auto_thumbs[thumbnail_name]['height']
                )
            return mark_safe(f'<img src="{url}" alt="{self.alt}" />')
        else:
            return 'No Image'

    #---------------------------------------------------------------------------
    def __str__(self):
        image_name = 'Untitled Image'
        if self.image and self.image_basename:
            image_name = self.image_basename

        if self.folder:
            image_name = "%s/%s" % (self.folder.name, image_name)

        return image_name

    #---------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if self.id:
            self._delete_thumbs()

        if self.image:
            self.image_basename = self.basename()

        super().save(*args, **kwargs)

        if self.image.name and default_storage.exists(self.image.name):
            self._create_thumbs()

    #---------------------------------------------------------------------------
    def delete(self, *args, **kwargs):
        # Delete all of our thumbs
        self._delete_thumbs()

        # delete the main image.
        if self.image.name:
            self.image.delete()

        super().delete(*args, **kwargs)

    #---------------------------------------------------------------------------
    def _delete_thumbs(self):
        old_image_record = self.__class__.objects.get(id=self.id)
        if not old_image_record.image.name:
            return

        for thumbnail_name in self.auto_thumbs.keys():
            storage_name = old_image_record.image.variant_name(thumbnail_name)
            if default_storage.exists(storage_name):
                default_storage.delete(storage_name)

    #---------------------------------------------------------------------------
    def _create_thumbs(self):
        for thumbnail_name in self.auto_thumbs.keys():
            self.image.generate_variant(
                    thumbnail_name,
                    'thumbnail',
                    width=self.auto_thumbs[thumbnail_name]['width'],
                    height=self.auto_thumbs[thumbnail_name]['height']
                )

    #---------------------------------------------------------------------------
    def url(self):
        """Returns a full URI to this image
        """
        if self.image:
            return self.image.url
        else:
            return "No Url"

    #---------------------------------------------------------------------------
    def basename(self):
        """Returns the basename of the image. Example: file.gif
        """
        return os.path.basename(self.filename())

    #---------------------------------------------------------------------------
    def ext(self):
        """Returns the file extension without the period. Example: gif
        """
        return os.path.splitext(self.filename())[-1].split('.')[-1]

    #---------------------------------------------------------------------------
    def filename(self):
        return os.path.split(self.image.name)[-1]

    #---------------------------------------------------------------------------
    def get_variant(self):
        content_slot = getattr(self, '_content_slot', None)
        if not content_slot: return {}
        return getattr(content_slot, 'variant', {})
    variant = property(get_variant)

    #---------------------------------------------------------------------------
    def get_variant_info(self):
        content_slot = getattr(self, '_content_slot', None)
        if not content_slot: return {}
        return getattr(content_slot, 'variant_info', {})
    variant_info = property(get_variant_info)

    #---------------------------------------------------------------------------
    class Meta:
        abstract = True
        ordering = ('folder__name', 'image_basename')

#-------------------------------------------------------------------------------
class Image(ImageBase):
    link_url = models.CharField(
            max_length=255,
            blank=True,
            null=True,
            help_text="Optional Link URL"
        )


#-------------------------------------------------------------------------------
class File(ModelIsContentType):
    """Generic File model.
    """

    _upload_folder = 'content/file'
    file = FileField(max_length=1024, upload_to=_upload_folder,)
    caption = models.CharField(max_length=1024, blank=True, null=True)

    folder = models.ForeignKey(
        Folder,
        blank=True,
        null=True,
        related_name="files",
        on_delete=models.CASCADE,
    )

    file_basename = models.CharField(
            max_length=1024,
            null=True,
            blank=True,
            editable=False,
        )

    #---------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)

        self._old_file = self.file

    #---------------------------------------------------------------------------
    def __str__(self):
        return u'%s' % self.file

    #---------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if self._old_file and self.file != self._old_file:
            # Remove our old file when a new one is being offered for replacement.
            self._old_file.storage.delete(self._old_file.name)

        if self.file:
            self.file_basename = self.basename()

        super(File, self).save(*args, **kwargs)

    #---------------------------------------------------------------------------
    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete(save=False)

        super(File, self).delete(*args, **kwargs)

    #---------------------------------------------------------------------------
    def url(self):
        """Returns a full URI to this file
        """
        return self.file.url

    #---------------------------------------------------------------------------
    def ext(self):
        """Returns the file extension without the period. Example: pdf
        """
        return os.path.splitext(self.filename())[-1].split('.')[-1]

    #---------------------------------------------------------------------------
    def basename(self):
        """Returns the basename of the file. Example: file.gif
        """
        return os.path.basename(self.filename())

    #---------------------------------------------------------------------------
    def filename(self):
        return self.file.path.rsplit('/', 1)[-1]


#-------------------------------------------------------------------------------
class CheckFileFirstVariantDict(VariantDict):
    """
    A variant dict which does no queries if the image already exists.

    Otherwise it operates in the same way as the normal variant dict.
    """

    #---------------------------------------------------------------------------
    def __init__(self, image_slot, image_file, user_variant_crop=None):
        self.image_slot = image_slot
        self.image_file = image_file
        self.user_variant_crop = user_variant_crop or {}

    #---------------------------------------------------------------------------
    def __getitem__(self, key):
        slot_key = '{}-{}-{}'.format(
            self.image_slot.model_key(),
            self.image_slot.id,
            key,
        )

        variant_name = self.image_file.variant_name(slot_key)
        if default_storage.exists(variant_name):
            return default_storage.url(variant_name)

        image_type = self.image_slot.image_type
        if not image_type:
            return

        # Pre load all of the variant settings.
        for variant in image_type.variants.all():
            attributes = variant.attributes

            user_crop = self.user_variant_crop.get(variant.key) or {}
            if user_crop and attributes['algorithm'] == 'crop':
                attributes['algorithm'] = 'crop_and_scale'
                attributes['arguments'].update(user_crop)

            super(VariantDict, self).__setitem__(variant.key, attributes)

        # Generate the variant (but use our slot_key).
        attributes = dict.__getitem__(self, key)
        return self.image_file.generate_variant(
            slot_key,
            attributes['algorithm'],
            **attributes['arguments']
        ).replace(' ', '%20')


#-------------------------------------------------------------------------------
class CheckFileFirstVariantInfoDict(VariantInfoDict):
    """
    A variant size dict which does no queries if the image already exists.

    Otherwise it operates in the same way as the normal variant dict.
    """

    #---------------------------------------------------------------------------
    def __init__(self, image_slot, image_file, user_variant_crop=None):
        self.image_slot = image_slot
        self.image_file = image_file
        self.user_variant_crop = user_variant_crop or {}

    #---------------------------------------------------------------------------
    def __getitem__(self, key):
        slot_key = '{}-{}-{}'.format(
            self.image_slot.model_key(),
            self.image_slot.id,
            key,
        )

        variant_name = self.image_file.variant_name(slot_key)
        if default_storage.exists(variant_name):
            return self.get_info(slot_key)

        image_type = self.image_slot.image_type
        if not image_type:
            return

        # Pre load all of the variant settings.
        for variant in image_type.variants.all():
            attributes = variant.attributes

            user_crop = self.user_variant_crop.get(variant.key) or {}
            if user_crop and attributes['algorithm'] == 'crop':
                attributes['algorithm'] = 'crop_and_scale'
                attributes['arguments'].update(user_crop)

            super(VariantInfoDict, self).__setitem__(variant.key, attributes)

        # Generate the variant and then extract the image info.
        attributes = dict.__getitem__(self, key)
        return self.image_file.generate_variant(
            slot_key,
            attributes['algorithm'],
            **attributes['arguments']
        )
        return self.get_info(slot_key)


#-------------------------------------------------------------------------------
class ModelHasUserVariantCrop(models.Model):

    # Stores any specific crop parameters defined by the user for variants.
    user_variant_crop = JSONField(null=True, blank=True)

    #---------------------------------------------------------------------------
    class Meta:
        abstract = True


#-------------------------------------------------------------------------------
class ModelHasCroppableImageField(ModelHasUserVariantCrop):
    """
    Adds machinery to a model to be able to store user specified crops for image fields.
    """

    #---------------------------------------------------------------------------
    class Meta:
        abstract = True

    #---------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(ModelHasCroppableImageField, self).__init__(*args, **kwargs)
        self.__old_image = str(self.image)

    #---------------------------------------------------------------------------
    def get_variant(self):
        if getattr(self, '_variant_cache', None):
            return self._variant_cache

        self._variant_cache = VariantDict(self.image, self.user_variant_crop)
        for key, value in self.image.field.variants.items():
            self._variant_cache[key] = copy.deepcopy(value)

        return self._variant_cache
    variant = property(get_variant)

    #---------------------------------------------------------------------------
    def get_variant_info(self):
        if getattr(self, '_variant_info_cache', None):
            return self._variant_info_cache

        self._variant_info_cache = VariantInfoDict(self.image, self.user_variant_crop)
        for key, value in self.image.field.variants.items():
            self._variant_info_cache[key] = copy.deepcopy(value)

        return self._variant_info_cache
    variant_info = property(get_variant_info)

    #---------------------------------------------------------------------------
    def delete_variants(self):
        """
        Deletes all of the variants that the models image field knows about.
        """
        for key, value in self.image.field.variants.items():
            filename = self.image.variant_name(key)
            if default_storage.exists(filename):
                default_storage.delete(filename)

    #---------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        # When the image changes, clear out any previous custom cropping.
        if str(self.image) != self.__old_image:
            self.user_variant_crop = {}

        super(ModelHasCroppableImageField, self).save(*args, **kwargs)


#-------------------------------------------------------------------------------
class AbstractImageSlot(ModelHasUserVariantCrop):
    image = models.ForeignKey(
        Image,
        related_name='slots',
        on_delete=models.CASCADE,
    )

    objects = WithRelated('image')

    #---------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.__old_image = self.image
        except Image.DoesNotExist as e:
            self.__old_image = None

    #---------------------------------------------------------------------------
    def model_key(self):
        """A project unique key representing this model.

        This key is used to prevent cropping collisions. It will show up in the
        filename path.
        """
        raise NotImplementedError('Must be implemented by sub-classes')

    #---------------------------------------------------------------------------
    def url(self):
        if self.image:
            return self.image.url()
        else:
            return ''

    #---------------------------------------------------------------------------
    def get_alt(self):
        if self.image:
            return self.image.alt
        else:
            return ''
    alt = property(get_alt)

    #---------------------------------------------------------------------------
    def get_caption(self):
        if self.image:
            return self.image.caption
        else:
            return ''
    caption = property(get_caption)

    #---------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        """
        Whenever a ImageSlot is saved we update the associated thumbs.

        Generate any new thumbs that are needed.
        """

        # When the image changes, clear out any previous custom cropping.
        if self.__old_image != self.image:
            self.user_variant_crop = {}

        super().save(*args, **kwargs)
        self._create_variants()

    #---------------------------------------------------------------------------
    def delete(self, *args, **kwargs):
        """
        Whenever a ImageSlot is deleted we also must delete the thumbs.
        """
        self.delete_variants()
        super().delete(*args, **kwargs)

    #---------------------------------------------------------------------------
    def delete_variants(self):
        """
        Deletes all of the variants that this image type knows about.
        """

        if not self.image:
            return

        image_type = self.image_type
        if not image_type:
            return

        for variant in image_type.variants.all():
            slot_key = '{}-{}-{}'.format(
                self.model_key(),
                self.id,
                variant.key,
            )

            filename = self.image.image.variant_name(slot_key)
            if default_storage.exists(filename):
                default_storage.delete(filename)

    #---------------------------------------------------------------------------
    def get_image_type(self):
        raise NotImplementedError('Must be implemented by sub-classes')
    image_type = property(get_image_type)

    #---------------------------------------------------------------------------
    def _create_variants(self):
        if not self.image:
            return

        if not self.image.image.name:
            return

        image_type = self.image_type
        if not image_type:
            return

        for variant in image_type.variants.filter(
            jit_generation=False
        ):
            self.variant[variant.key]

    #---------------------------------------------------------------------------
    def get_variant(self):
        """
        Returns a dictionary of variant urls keyed by their key.

        The dictionary returned is a specialization that will generate the
        variant images on demand.
        """
        if not self.image:
            return {}

        if getattr(self, '_variant_cache', None):
            return self._variant_cache

        self._variant_cache = CheckFileFirstVariantDict(
            self, self.image.image, self.user_variant_crop
        )
        return self._variant_cache
    variant = property(get_variant)

    #---------------------------------------------------------------------------
    def get_variant_info(self):
        """
        Returns a dictionary of variant sizes keyed by their key.

        The dictionary returned is a specialization that will generate the
        variant images on demand.
        """
        if not self.image:
            return {}

        if getattr(self, '_variant_info_cache', None):
            return self._variant_info_cache

        self._variant_info_cache = CheckFileFirstVariantInfoDict(
            self, self.image.image, self.user_variant_crop
        )
        return self._variant_info_cache
    variant_info = property(get_variant_info)

    #---------------------------------------------------------------------------
    class Meta:
        abstract = True


#-------------------------------------------------------------------------------
class ImageSlot(AbstractImageSlot, ContentSlot):

    #---------------------------------------------------------------------------
    def model_key(self):
        return 'image'

    #---------------------------------------------------------------------------
    def get_image_type(self):
        """
        Return the ImageType instance that defines the cropping.
        """

        type = self.content_object.get_type()
        try:
            csm = type.get_interface(self.key)
            return ImageType.objects.get(
                _swim_content_type__title=csm['swim_content_type']
            )
        except (ImageType.DoesNotExist, ContentSchemaMember.DoesNotExist, TypeError):
            return None

    image_type = property(get_image_type)

    #---------------------------------------------------------------------------
    class Meta:
        verbose_name_plural = 'Images'
        ordering = ['order']

register_atom_type('image', ReferencedAtomType(Image, ImageSlot))


#-------------------------------------------------------------------------------
class FileSlot(ContentSlot):
    file = models.ForeignKey(
        File,
        related_name='slots',
        on_delete=models.CASCADE,
    )

    objects = WithRelated('file')

    class Meta:
        verbose_name_plural = "Files"
        ordering = ['order',]

register_atom_type(
        'file',
        ReferencedAtomType(File, FileSlot)
    )

#-------------------------------------------------------------------------------
class FolderSlot(ContentSlot):
    folder = models.ForeignKey(
        Folder,
        related_name='slots',
        on_delete=models.CASCADE
    )

    objects = WithRelated('folder')

    class Meta:
        verbose_name_plural = "Folders"
        ordering = ['order',]

register_atom_type(
        'folder',
        ReferencedAtomType(Folder, FolderSlot)
    )

#-------------------------------------------------------------------------------
class ImageType(KeyedType):
    """
    Defines an image type that comes with a specific set of sub-images.
    """

    #---------------------------------------------------------------------------
    @property
    def crop_variants(self):
        return self.variants.filter(algorithm='crop')


IMAGE_VARIANT_ALGORITHMS = (
    ('thumbnail', 'thumbnail',),
    ('crop', 'crop',),
)

#-------------------------------------------------------------------------------
class ImageVariant(ModelBase):
    """
    Defines a named variant of a given image.
    Defines a single choice within an EnumType.

    attributes:
    image_type
        The FK Reference to its parent ImageType.
    algorithm
        The name of the algorithm used to generate this variant.
    arguments
        The json args given to the algorithm to generate this variant.
    jit_generation
        A boolean argument that indicates whether this variant should be
        generated a soon as an image is uploaded, or if it should wait until
        it is accessed.
    """

    image_type = models.ForeignKey(
        ImageType,
        related_name="variants",
        on_delete=models.CASCADE,
    )
    key = modelfields.Key(max_length=200, unique=True)

    algorithm = models.CharField(
        max_length=255,
        choices=IMAGE_VARIANT_ALGORITHMS,
    )
    arguments = models.CharField(
        max_length=255,
        default='{"width": XXX, "height": XXX}',
        help_text="""
            Value must be valid JSON.
        """
    )
    documentation = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Document where this variant is used in the project.",
    )
    jit_generation = models.BooleanField(
        default=False,
        help_text="""
        If you set this to true, then this variant will only be generated
        Just In Time. In other words, it will be generated the first time
        it is accessed.
        """
    )

    class Meta:
        unique_together = (("key", "image_type"),)

    def __str__(self):
        base_str = u"%s: %s(%s)" % (self.key, self.algorithm, self.arguments)
        return base_str

    #---------------------------------------------------------------------------
    def get_attributes(self):
        arguments = self._arguments()
        return {
            'documentation': self.documentation,
            'algorithm': self.algorithm,
            'jit_generation': self.jit_generation,
            'arguments': arguments,
        }
    attributes = property(get_attributes)

    #---------------------------------------------------------------------------
    def _arguments(self):
        return json.loads(self.arguments)

    #---------------------------------------------------------------------------
    def url(self, image_model_instance):
        return default_storage.url(self.name(image_model_instance))

    #---------------------------------------------------------------------------
    def name(self, image_model_instance):
        """
        Returns the name that will be used for this variant.

        Names are based on the variant ID - which the user can't change.

        Example:
            content/image/311-124559/original-variants/<key>.jpg
        """
        if not image_model_instance.image.name:
            return
        addition = "%s" % (self.key,)
        return image_model_instance.image.variant_name(addition)

