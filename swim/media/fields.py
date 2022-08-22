import datetime
import os
from PIL import Image

from django.db.models import  (
    ImageField as DjangoImageField,
    FileField as DjangoFileField,
    signals
)
from django.db.models.fields.files import (
    ImageFieldFile as DjangoImageFieldFile,
    FieldFile as DjangoFieldFile
)
from django.utils.deconstruct import deconstructible
from django.core.files.base import ContentFile

from swim.media.formfields import ImageField as FormImageField
from swim.media import image


#-------------------------------------------------------------------------------
class VariantDict(dict):
    """
    Dict specialization for variants which lazily generates them when accessed.
    """

    #---------------------------------------------------------------------------
    def __init__(self, image_file, user_variant_crop=None):
        self.image_file = image_file
        self.user_variant_crop = user_variant_crop or {}

    #---------------------------------------------------------------------------
    def __getitem__(self, key):
        attributes = super(VariantDict, self).__getitem__(key)

        # If the user has specified an exact crop, use it.
        user_crop = self.user_variant_crop.get(key) or {}
        if user_crop and attributes['algorithm'] == 'crop':
            attributes['algorithm'] = 'crop_and_scale'
            attributes['arguments'].update(user_crop)

        return self.image_file.generate_variant(
            key,
            attributes['algorithm'],
            **attributes['arguments']
        ).replace(" ", "%20") # needed for valid HTML


#-------------------------------------------------------------------------------
class VariantInfoDict(dict):
    """
    Dict specialization for variants which lazily generates them when accessed.

    This one returns the size as a dict {"width": xxx, "height": xxx} instead
    of the actual image url
    """

    #---------------------------------------------------------------------------
    def __init__(self, image_file, user_variant_crop=None):
        self.image_file = image_file
        self.user_variant_crop = user_variant_crop or {}

    #---------------------------------------------------------------------------
    def get_info(self, key):
        variant_name = self.image_file.variant_name(key)
        image_path = self.image_file.storage.path(variant_name)
        img = Image.open(image_path)
        return {
            "size": {
                "width": img.size[0],
                "height": img.size[1],
            }
        }

    #---------------------------------------------------------------------------
    def __getitem__(self, key):
        attributes = super(VariantInfoDict, self).__getitem__(key)

        # If the user has specified an exact crop, use it.
        user_crop = self.user_variant_crop.get(key) or {}
        if user_crop and attributes['algorithm'] == 'crop':
            attributes['algorithm'] = 'crop_and_scale'
            attributes['arguments'].update(user_crop)

        # Generate image
        self.image_file.generate_variant(
            key,
            attributes['algorithm'],
            **attributes['arguments']
        )
        return self.get_info(key)


#-------------------------------------------------------------------------------
class ImageFieldFile(DjangoImageFieldFile):

    #---------------------------------------------------------------------------
    def formfield(self, **kwargs):
        # This is a fairly standard way to set up some defaults
        # while letting the caller override them.
        defaults = {'form_class': FormImageField}
        defaults.update(kwargs)
        return super(ImageField, self).formfield(**defaults)

    #---------------------------------------------------------------------------
    def variant_dirname(self):
        """
        Returns the appropriate variant dirname to MEDIA_ROOT path base on name.

        Variant names are based on the original image path.  Assuming the
        upload path is: content/image, the following are examples:
            original: content/image/<creation-date>/<original_name>.<original_extension>
            original-example: content/image/001-121111/upload.jpg
            variant: content/image/<creation-date>/<original_name>-variants/
            variant-example: content/image/001-121111/upload-variants/
        """
        path, ext = os.path.splitext(self.name)
        return path+"-variants"

    #---------------------------------------------------------------------------
    def variant_name(self, name):
        """
        Returns the appropriate variant relative to MEDIA_ROOT path base on name.

        Variant names are based on the original image path.  Assuming the
        upload path is: content/image, the following are examples:
            original: content/image/<creation-date>/<original_name>.<original_extension>
            original-example: content/image/001-121111/upload.jpg
            variant: content/image/<creation-date>/<original_name>-variants/<variantname>/<original-name>.<original_extension>
            variant-example: content/image/001-121111/upload-variants/adminthumb/upload.jpg
        """
        path, filename = os.path.split(self.name)
        return os.path.join(self.variant_dirname(), name, filename)

    #---------------------------------------------------------------------------
    def generate_variant(self, name, algorithm, **arguments):
        """
        Generate a variant name using the algorithm and parameters.
        """
        variant_name = self.variant_name(name)
        try:

            # TODO: This should be a bit smarter in determining whether we need
            #       to create the image or not.

            # Optionally create the image.
            if not self.storage.exists(variant_name):
                input_fd = self.storage.open(self.name, mode='rb')

                # Save a temporary file to the variant directory to make sure it is created.
                self.storage.save(variant_name, ContentFile('1'))

                # Which we can then overwrite with our new image.
                output_fd = self.storage.open(variant_name, mode='wb')

                if algorithm == 'crop_and_scale':
                    image.backend.crop_and_scale(
                        input_fd, output_fd, **arguments,
                    )

                elif algorithm in ('thumbnail', 'thumb'):
                    image.backend.fit(
                        input_fd, output_fd, **arguments
                    )

                elif algorithm == 'crop':
                    image.backend.fit_crop(
                        input_fd, output_fd, **arguments
                    )

            return self.storage.url(variant_name)

        except Exception as e:
            # The file doesn't exist or we're having issues.

            # If we didn't manage to properly create the image,
            # then delete it!
            if self.storage.exists(variant_name):
                self.storage.delete(variant_name)

            # TODO: this shouldn't be hard coded like so.
            return "/static/swim/images/empty-image.png"

    #---------------------------------------------------------------------------
    def get_variant(self):
        """
        Returns a dictionary of variant urls keyed by their key.

        The dictionary returned is a specialization that will generate the
        variant images on demand.
        """
        if getattr(self, '_variant_cache', None):
            return self._variant_cache

        self._variant_cache = VariantDict(self)

        for key, attributes in self.field.variants.items():
            self._variant_cache[key] = attributes
        return self._variant_cache
    variant = property(get_variant)

    #---------------------------------------------------------------------------
    def get_variant_info(self):
        """
        Returns a dictionary of variant sizes keyed by their key.

        The dictionary returned is a specialization that will generate the
        variant images on demand.
        """
        if getattr(self, '_variant_info_cache', None):
            return self._variant_info_cache

        self._variant_info_cache = VariantInfoDict(self)

        for key, attributes in self.field.variants.items():
            self._variant_info_cache[key] = attributes
        return self._variant_info_cache
    variant_info = property(get_variant_info)

    #---------------------------------------------------------------------------
    def save(self, name, content, save=True):
        super(ImageFieldFile, self).save(name, content, save=save)
        self.field.create_eager_variants(self.instance)

    #---------------------------------------------------------------------------
    def delete(self, save=True):
        """
        Override the default method to ensure ALL of our variants are deleted.
        """
        variant_dirname = self.variant_dirname()
        if self.storage.exists(variant_dirname):
            dirs, files = self.storage.listdir(variant_dirname)

            for file in files:
                self.storage.delete(os.path.join(variant_dirname, file))

            for dir in dirs:
                _, files = self.storage.listdir(os.path.join(variant_dirname, dir))
                for file in files:
                    self.storage.delete(os.path.join(variant_dirname, dir, file))

        if self.storage.exists(self.name):
            self.storage.delete(self.name)

        super(ImageFieldFile, self).delete(save)
    delete.alters_data = True


#-------------------------------------------------------------------------------
class FileField(DjangoFileField):
    """
    """
    attr_class = DjangoFieldFile


#-------------------------------------------------------------------------------
@deconstructible
class EnsureExtension:
    """
    An upload_to that will ensure the image has the appropriate extension.
    """

    #---------------------------------------------------------------------------
    def __init__(self, upload_to, field):
        self.upload_to = upload_to
        self.field = field

    #---------------------------------------------------------------------------
    def set_image_attr_name(self, image_attr_name):
        self.image_attr_name = image_attr_name

    #---------------------------------------------------------------------------
    def __call__(self, instance, filename):
        if callable(self.upload_to):
            base = self.upload_to(instance, filename)
        else:
            base = self.generate_filename(instance, filename)

        head, tail = os.path.split(base)
        if not tail:
            tail = filename

        image_field = getattr(instance, self.image_attr_name)
        name, ext = os.path.splitext(os.path.basename(tail))
        if not ext and image_field:
            from PIL import Image as PILImage
            image_field.open("rb")
            x = PILImage.open(image_field)
            if x.format:
                ext = ".%s" % x.format.lower()

        # Remove any ? and # form the filename
        filename = os.path.join(head, name + ext)
        filename = filename.replace("#", "")
        filename = filename.replace("?", "")
        return filename

    #---------------------------------------------------------------------------
    def get_directory_name(self):
        return os.path.normpath(str(datetime.datetime.now().strftime(str(self.upload_to))))

    #---------------------------------------------------------------------------
    def generate_filename(self, instance, filename):
        return os.path.join(self.get_directory_name(), filename)


#-------------------------------------------------------------------------------
class ModelContribution:
    """
    A callable that allows additional image variants to be specified at runtime.
    """
    def __init__(self, callable):
        self.callable = callable

    def __call__(self, *args, **kwargs):
        return self.callable(*args, **kwargs)


#-------------------------------------------------------------------------------
class ImageField(DjangoImageField):
    """
    Image field with facilities to define variants.
    """
    attr_class = ImageFieldFile

    #---------------------------------------------------------------------------
    def __init__(self, variants=None, **kwargs):
        self.upload_to_original = kwargs['upload_to']
        self.upload_to = kwargs['upload_to'] = EnsureExtension(kwargs.get('upload_to', ''), self)
        self.variants = variants or {}
        super(ImageField, self).__init__(**kwargs)

    #---------------------------------------------------------------------------
    def contribute_to_class(self, cls, name):
        self.attr_name = name
        self.upload_to.set_image_attr_name(name)
        setattr(cls, 'add_%s_variant' % name, ModelContribution(self.add_variant))
        signals.post_save.connect(self.create_eager_variants, sender=cls)
        return super(ImageField, self).contribute_to_class(cls, name)

    #---------------------------------------------------------------------------
    def create_eager_variants(self, instance, **kwargs):
        for name, attributes in self.variants.items():
            if not attributes['jit_generation']:
                image_field = getattr(instance, self.attr_name)
                if image_field:
                    image_field.generate_variant(
                            name,
                            attributes['algorithm'],
                            **attributes['arguments']
                        )

    #---------------------------------------------------------------------------
    def add_variant(self, name, algorithm, arguments, jit_generation=False):
        self.variants[name] = {
                'algorithm': algorithm,
                'arguments': arguments,
                'jit_generation': jit_generation,
            }

    #---------------------------------------------------------------------------
    def deconstruct(self):
        name, path, args, kwargs = super(ImageField, self).deconstruct()
        if self.variants is not None:
            kwargs['variants'] = self.variants

        kwargs['upload_to'] = self.upload_to_original
        return name, path, args, kwargs

