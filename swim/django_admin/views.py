
import os.path
from django.conf import settings

from PIL import Image

from ckeditor_uploader import views
from django.views.decorators.csrf import csrf_exempt

from ckeditor_uploader.utils import storage

#-------------------------------------------------------------------------------
class ImageUploadView(views.ImageUploadView):

    #---------------------------------------------------------------------------
    @staticmethod
    def _save_file(request, uploaded_file):
        filename = views.get_upload_filename(uploaded_file.name, request.user)

        img_name, img_format = os.path.splitext(filename)
        IMAGE_QUALITY = getattr(settings, "CKEDITOR_IMAGE_QUALITY", 60)
        IMAGE_MAX_SIZE = getattr(settings, "CKEDITOR_IMAGE_MAX_SIZE", (600, 600))
        MEDIA_ROOT = getattr(settings, "MEDIA_ROOT", '')

        if str(img_format).lower() in ('.jpg', '.jpeg', '.png'):
            img = Image.open(uploaded_file)
            img.thumbnail(IMAGE_MAX_SIZE, Image.ANTIALIAS)
            saved_path = storage.save(filename, uploaded_file)
            img.save(os.path.join(MEDIA_ROOT, saved_path), quality=IMAGE_QUALITY, optimize=True)

        else:
            saved_path = storage.save(filename, uploaded_file)

        return saved_path

upload = csrf_exempt(ImageUploadView.as_view())

