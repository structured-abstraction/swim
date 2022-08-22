"""
Provides the appropriate backends to modifying images.

"""

from django.utils.functional import LazyObject
from importlib import import_module

from django.conf import settings

from PIL import Image

#-------------------------------------------------------------------------------
class ImageInterface:

    #---------------------------------------------------------------------------
    @classmethod
    def fit_crop(cls, input_fd, output_fd, left, right, top, bottom, width, height):
        """
        Crops an image using exact coordinates and scales the result to a final size.

        arguments:
            input_fd: the fd pointing to the input filename.
            output_fd: the fd pointing to the output filename.
            left, right, top, bottom: Coordinates on the source image to crop.
            width, height: The desired width / height of the new image.
        """

        raise NotImplementedError

    #---------------------------------------------------------------------------
    @classmethod
    def fit_crop(cls, input_fd, output_fd, width=None, height=None):
        """
        Does a resize/crop operation that minimizes information cropped by resizing first.

        arguments:
            input_fd: the fd pointing to the input filename.
            output_fd: the fd pointing to the output filename.
            width: the desired width of the new image.
            height: the desired height of the new image.
        """
        raise NotImplementedError

    #---------------------------------------------------------------------------
    @classmethod
    def fit(cls, input_fd, output_fd, width=None, height=None, antialias=True):
        """
        Does a simple resize operation that preserves aspect ratio.

        arguments:
            input_fd: the fd pointing to the input filename.
            output_fd: the fd pointing to the output filename.
            width: the desired width of the new image.
            height: the desired height of the new image.
        """
        raise NotImplementedError

#-------------------------------------------------------------------------------
class PILWrapper(ImageInterface):

    #---------------------------------------------------------------------------
    @classmethod
    def crop_and_scale(cls,
        input_fd, output_fd,
        left, right, top, bottom, width, height,
        antialias=True
    ):
        img = Image.open(input_fd)
        format = img.format

        # Crop the image.
        img = img.crop((left, top, right, bottom))

        # Resize the cropped image to the final size.
        filter = Image.NEAREST
        if antialias:
            filter = Image.ANTIALIAS
        img = img.resize((width, height), filter)

        cls._optimized_save(output_fd, img, format)

    #---------------------------------------------------------------------------
    @classmethod
    def fit_crop(cls, input_fd, output_fd, width=None, height=None, antialias=True):
        img = Image.open(input_fd)
        format = img.format

        original_width, original_height = float(img.size[0]), float(img.size[1])

        # Use the original size if no size given
        width = float(width or original_width)
        height = float(height or original_height)

        # If the desired size fits completely within the original image, we'l
        # downsize the image before cropping it in order to minimize the amount of
        # image that we cut out.
        scale = max(width/original_width, height/original_height)
        if (scale < 1):
            original_width = int(original_width * scale)
            original_height = int(original_height * scale)
            # Resize and save it.
            filter = Image.NEAREST
            if antialias:
                filter = Image.ANTIALIAS
            img = img.resize((original_width, original_height), filter)

        # Avoid enlarging the image
        width = min(width, original_width)
        height = min(height, original_height)

        # Define the cropping box
        left = int((original_width - width) / 2)
        top = int((original_height - height) / 2)
        right = int(left + width)
        bottom = int(top + height)

        # Crop and save it.
        img = img.crop((left, top, right, bottom))
        cls._optimized_save(output_fd, img, format)

    #---------------------------------------------------------------------------
    @classmethod
    def fit(cls, input_fd, output_fd, width=None, height=None, antialias=True):
        img = Image.open(input_fd)
        format = img.format

        # Replace width and height by the maximum values
        w = int(width or img.size[0])
        h = int(height or img.size[1])

        # Resize and save it.
        filter = Image.NEAREST
        if antialias:
            filter = Image.ANTIALIAS
        img.thumbnail((w, h), filter)
        cls._optimized_save(output_fd, img, format)

    #---------------------------------------------------------------------------
    @classmethod
    def _optimized_save(cls, output_fd, img, format):
        format = format.upper()
        kwargs = {}
        default_target_mode = "RGB"
        if format == "JPG" or format == "JPEG":
            kwargs = {
                    "optimize": getattr(settings, "SWIM_MEDIA_JPEG_OPTIMIZE", True),
                    "quality": getattr(settings, "SWIM_MEDIA_JPEG_QUALITY", 90),
                }
        elif format == "GIF":
            kwargs = {
                    "optimize": getattr(settings, "SWIM_MEDIA_PNG_OPTIMIZE", True),
                }
        elif format == "PNG":
            default_target_mode = "RGBA"

        if img.mode not in ("RGBA", "RGB"):
            img = img.convert(default_target_mode)
        img.save(output_fd, img.format, **kwargs)

#-------------------------------------------------------------------------------
def get_backend_class(import_path=None):
    if import_path is None:
        import_path = settings.SWIM_IMAGE_BACKEND

    try:
        dot = import_path.rindex('.')
    except ValueError:
        raise ImproperlyConfigured("%s isn't a image backend module." % import_path)
    module, classname = import_path[:dot], import_path[dot+1:]
    try:
        mod = import_module(module)
    except ImportError as e:
        raise ImproperlyConfigured('Error importing image backend module %s: "%s"' % (module, e))
    try:
        return getattr(mod, classname)
    except AttributeError:
        raise ImproperlyConfigured('Image Module module "%s" does not define a "%s" class.' % (module, classname))

#-------------------------------------------------------------------------------
class DefaultBackend(LazyObject):
    def _setup(self):
        self._wrapped = get_backend_class()()

#-------------------------------------------------------------------------------
backend = DefaultBackend()

