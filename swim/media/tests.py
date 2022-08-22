import tempfile
import os

from django.conf import settings
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.core.files.storage import default_storage
from django.core import files
from django.urls import reverse
from django.template import Template, Context
from django.test import override_settings
from django.utils.encoding import smart_bytes


import swim

from swim.core.models import (
    ContentSchema,
    ContentSchemaMember,
    ResourceType,
)

# It's a bit wierd that the tests depend on the content app,
# But we needed a resource to test against.
from swim.content.models import Page

from swim.test import TestCase
from swim.media.models import (
    Image,
    File,
    ImageType,
    ImageVariant,
    ImageSlot,

)
from swim.media.image import PILWrapper
from swim.media.views import image_thumb

import PIL

module_dirname, _ = os.path.split(swim.__file__)
#-------------------------------------------------------------------------------
@override_settings(
        MEDIA_ROOT=module_dirname,
        SWIM_MEDIA_JPEG_OPTIMIZE=True,
        SWIM_MEDIA_JPEG_QUALITY=90,
    )
class ImageTestBase(TestCase):
    #---------------------------------------------------------------------------
    def _upload_test_file(self, path, model, field_name):
        """Simulates an upload operation of an image to an ImageField

        Arguments:
        path - Relative path to the swim module of where to find the image to upload
        model - An instance of a model that has an Image field attached to it
        field_name - The name of the Image field on model.
        """

        # Prepend the path to the swim module to whatever was given in path
        dirname, filename = os.path.split(path)
        module_dirname, _ = os.path.split(swim.__file__)
        dirname = os.path.abspath(os.path.join(module_dirname, dirname))
        path = os.path.join(dirname, filename)

        # Dump the raw contents of the image into the image field
        raw_contents = open(path, 'rb')
        file = getattr(model, field_name)
        file.save(raw_contents.name, files.File(raw_contents), save=True)
        return file.path



#-------------------------------------------------------------------------------
@override_settings(
    ROOT_URLCONF='swim.urls',
    MEDIA_URL='http://localhost:8000/',
)
class ImageTest(ImageTestBase):
    #Bundle of tests that exercise the swim.media.Image model

    def setUp(self):
        # Create a new Image
        self.image = Image.objects.create(
            alt='The best eagle image ever'
        )
        # Upload a test image to the Model
        self._upload_test_file(
            'content/tests/files/image.gif',
            self.image,
            'image'
        )

    def tearDown(self):
        self.image.delete()

    def test_ext(self):
        #The ext must give back the string after the last '.'
        self.assertEqual(self.image.ext(), 'gif')

    def test_filename(self):
        #The filename must give back only the file name
        self.assertEqual(self.image.filename(), 'image.gif')

    def test_admin_thumbnail(self):
        url = "http://localhost:8000/content/image/%y%m%d-%H%M%S/image-variants/admin-thumb.gif"
        url = self.image.creationdate.strftime(url)
        expected_image = '<img src="%s" alt="The best eagle image ever" />' % (url)
        self.assertEqual(self.image.admin_thumbnail(), expected_image)


#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class ImageDeletionTests(ImageTestBase):
    #Bundle of tests that exercise the swim.media.Image model

    def test_image_id_dir_deleted(self):
        # Create a new Image
        self.image = Image.objects.create(
            alt = 'The best eagle image ever'
        )

        path = "asdf"
        try:
            # Upload a test image to the Model
            self._upload_test_file(
                'content/tests/files/image.gif',
                self.image,
                'image'
            )
            path = self.image.image.path

        finally:
            # Delete the image record
            self.image.delete()

        # Ensure the image/<id>. dir does not exist.
        self.assertFalse(default_storage.exists(path))


    def test_thumbnail_deleted(self):
        # Create a new Image
        self.image = Image.objects.create(
            alt = 'The best eagle image ever'
        )
        try:
            # Upload a test image to the Model
            self._upload_test_file(
                'content/tests/files/image.gif',
                self.image,
                'image'
            )


            # After uploading the image an admin thumbnail must have been
            # created.
            thumbnail_name = self.image.image.variant_name('admin-thumb')

            # Ensure the image and the thumbs exist.
            self.assertTrue(default_storage.exists(thumbnail_name))

        finally:
            # Delete the image record
            self.image.delete()

        # Ensure the image and the thumbs don't exist.
        self.assertFalse(default_storage.exists(thumbnail_name))


#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class TestFileRemnants(ImageTestBase):
    def setUp(self):
        super(TestFileRemnants, self).setUp()
        # a set to keep track of files we create
        self.filename_set = set()

    def tearDown(self):
        super(TestFileRemnants, self).tearDown()

        # cleanup the filenames that we created.
        for filename in self.filename_set:
            if default_storage.exists(filename):
                os.remove(filename)

    #---------------------------------------------------------------------------
    def _save_file(self, path, model, field_name):
        dirname, filename = os.path.split(path)
        module_dirname, _ = os.path.split(swim.__file__)
        dirname = os.path.abspath(os.path.join(module_dirname, dirname))
        path = os.path.join(dirname, filename)
        raw_contents = open(path, 'rb')
        file = getattr(model, field_name)
        file.save(raw_contents.name, files.File(raw_contents), save=True)
        return file.path

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class FileTest(ImageTestBase):
    #Bundle of tests that exercise the swim.media.File model

    def setUp(self):
        # Create a new File
        self.file = File.objects.create()
        # Upload a test file to the Model
        self._upload_test_file(
            'content/tests/files/image.gif',
            self.file,
            'file'
        )

    def tearDown(self):
        # Remove the test file after every test
        if default_storage.exists(self.file.file.path):
            os.remove(self.file.file.path)

    def test_url(self):
        #The url must give back the full URI including http://www.hostname.com/
        name = self.file.file.name
        if name.startswith("/"):
            name = name[1:]
        self.assertEqual(self.file.url(), settings.MEDIA_URL + name)

    def test_ext(self):
        #The ext must give back the string after the last '.'
        self.assertEqual(self.file.ext(), 'gif')

    def test_filename(self):
        #The filename must give back only the file name
        basedir, filename = os.path.split(self.file.file.name)
        self.assertEqual(self.file.filename(), filename)

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class ImageInterfaceTests(ImageTestBase):
    #---------------------------------------------------------------------------
    def setUp(self):
        super(ImageInterfaceTests, self).setUp()
        self.image_test_directory = tempfile.mkdtemp()

    #---------------------------------------------------------------------------
    def tearDown(self):
        # Remove all of the files we create.
        for dirpath, dirnames, filenames in os.walk(self.image_test_directory, topdown=False):
            for filename in filenames:
                os.unlink(os.path.join(dirpath, filename))
            for dirname in dirnames:
                os.rmdir(os.path.join(dirpath, dirname))
        os.rmdir(self.image_test_directory)

    #---------------------------------------------------------------------------
    def _8x8_white_image_with_black_centre(self, name):
        img = PIL.Image.new("RGB", (8,8))
        white = (255,255,255)
        black = (0,0,0)
        pixels = [
            [white, white, white, white, white, white, white, white],
            [white, white, white, white, white, white, white, white],
            [white, white, black, black, black, black, white, white],
            [white, white, black, black, black, black, white, white],
            [white, white, black, black, black, black, white, white],
            [white, white, black, black, black, black, white, white],
            [white, white, white, white, white, white, white, white],
            [white, white, white, white, white, white, white, white],

        ]
        for x, color_row in enumerate(pixels):
            for y, color in enumerate(color_row):
                img.putpixel((x,y), color)
        filepath = os.path.join(self.image_test_directory, name)
        img.save(filepath)
        return open(filepath, "rb")

    def _test_resize(self, backend):
        input_fd = self._8x8_white_image_with_black_centre("orig.jpg")
        output_filename = os.path.join(self.image_test_directory, "fit.jpg")
        output_fd = open(output_filename, "wb")
        backend.fit(input_fd, output_fd, 4, 4, antialias=False)

        output_fd.close()
        result = PIL.Image.open(output_filename)
        self.assertEqual(result.size[0], 4)
        self.assertEqual(result.size[1], 4)
        # this pixel should be approximately black
        pixel = result.getpixel((1,1))
        # The antialiasing keeps changing on us and more of the black keeps leaking ot the side
        # pixels. Not sure what to do about that. 18 is low enough for now.
        self.assertTrue(pixel[0] < 18)
        self.assertTrue(pixel[1] < 18)
        self.assertTrue(pixel[2] < 18)

    def _test_fit_crop(self, backend):
        input_fd = self._8x8_white_image_with_black_centre("orig.jpg")
        output_filename = os.path.join(self.image_test_directory, "crop.jpg")
        output_fd = open(output_filename, "wb")
        backend.fit_crop(input_fd, output_fd, 2, 4, antialias=False)

        output_fd.close()
        result = PIL.Image.open(output_filename)
        self.assertEqual(result.size[0], 2)
        self.assertEqual(result.size[1], 4)

        white_ish = 225

        # Top and bottom rows should be approximately white.
        for x in range(2):
            for y in [0,3]:
                pixel = result.getpixel((x,y))

                # Approximately white
                self.assertTrue(pixel[0] > white_ish)
                self.assertTrue(pixel[1] > white_ish)
                self.assertTrue(pixel[2] > white_ish)

        black_ish = 25
        for x in range(2):
            for y in range(1,3):
                pixel = result.getpixel((x,y))

                # Approximately black
                self.assertTrue(pixel[0] < black_ish)
                self.assertTrue(pixel[1] < black_ish)
                self.assertTrue(pixel[2] < black_ish)


#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class PILWrapperTests(ImageInterfaceTests):
    def test_resize(self):
        self._test_resize(PILWrapper)

    def test_fit_crop(self):
        self._test_fit_crop(PILWrapper)

#-------------------------------------------------------------------------------
@override_settings(
    ROOT_URLCONF='swim.urls',
    MEDIA_URL='http://localhost:8000/',
)
class ImageTypeTests(ImageTestBase):
    #---------------------------------------------------------------------------
    def setUp(self):
        super(ImageTypeTests, self).setUp()
        self.content_schema = ContentSchema.objects.create(title="New Page Type")
        self.resource_type = ResourceType.objects.create(
            key='new_type',
            title='New Page Type',
            content_schema=self.content_schema,
        )
        self.page = Page.objects.create(
                path="/image-type-variant-tests",
                resource_type=self.resource_type,
            )

    #---------------------------------------------------------------------------
    def _basic_thumbs_variant(self):
        self.type = ImageType.objects.create(
            key="basic_thumbs",
            title="Basic Thumbs",
        )
        self.variant = ImageVariant.objects.create(
            image_type=self.type,
            algorithm="Thumbnail",
            arguments='{"width": 128, "height": 64}',
            key="small_thumb",
        )
        self.jit_variant = ImageVariant.objects.create(
            image_type=self.type,
            algorithm="Thumbnail",
            arguments='{"width": 256, "height": 256}',
            key="large_thumb",
            jit_generation=True,
        )

        self.csm = ContentSchemaMember.objects.create(
                content_schema=self.content_schema,
                order=1,
                key='hero',
                title='Hero Image',
                cardinality='single',
                swim_content_type=self.type.swim_content_type(),
            )
        self.csm_list = ContentSchemaMember.objects.create(
                content_schema=self.content_schema,
                order=2,
                key='hero_list',
                title='Hero Image List',
                cardinality='list',
                swim_content_type=self.type.swim_content_type(),
            )

    #---------------------------------------------------------------------------
    def test_variants_created_on_save(self):
        self._basic_thumbs_variant()

        # Create a new Image
        self.image = Image.objects.create(
            alt = 'The best eagle image ever'
        )
        try:

            # Upload a test image to the Model
            self._upload_test_file(
                'content/tests/files/image.gif',
                self.image,
                'image'
            )
            small_thumb = self.variant.name(self.image)
            large_thumb = self.jit_variant.name(self.image)

            # Before it's been related to the appropriate resource
            # there is no resource type so no variants exist.
            self.assertFalse(default_storage.exists(large_thumb))
            self.assertFalse(default_storage.exists(small_thumb))

            ri = ImageSlot.objects.create(
                object_id=self.page.id,
                django_content_type=DjangoContentType.objects.get_for_model(self.page),
                order=1,
                key='hero',
                image=self.image,
            )
            try:


                # after relating it to a resource, the non-JIT variants should exist
                # and the JIT variants should NOT exist.
                self.assertFalse(default_storage.exists(large_thumb))
                self.assertTrue(default_storage.exists(small_thumb))


                # Only after the JIT variants are accessed, should they exist.
                large_thumb_url = ri.variant['large_thumb']
                self.assertTrue(large_thumb_url.endswith(large_thumb))
                self.assertTrue(default_storage.exists(large_thumb))
                self.assertTrue(default_storage.exists(small_thumb))

            finally:
                ri.delete()
            # Once we delete the associated with a particular resource the variants
            # should also be deleted.
            self.assertFalse(default_storage.exists(large_thumb))
            self.assertFalse(default_storage.exists(small_thumb))

        finally:
            self.image.delete()

    #---------------------------------------------------------------------------
    def test_template_api_for_resource_images(self):
        self._basic_thumbs_variant()

        # Create a new Image
        self.image = Image.objects.create(
            caption = 'Caption MOFO!',
            alt = 'The best eagle image ever'
        )
        try:

            # Upload a test image to the Model
            self._upload_test_file(
                'content/tests/files/image.gif',
                self.image,
                'image'
            )
            small_thumb = self.variant.name(self.image)
            large_thumb = self.jit_variant.name(self.image)

            # Before it's been related to the appropriate resource
            # there is no resource type so no variants exist.
            self.assertFalse(default_storage.exists(large_thumb))
            self.assertFalse(default_storage.exists(small_thumb))

            ri = ImageSlot.objects.create(
                object_id=self.page.id,
                django_content_type=DjangoContentType.objects.get_for_model(self.page),
                order=1,
                key='hero',
                image=self.image,
            )
            ri2 = ImageSlot.objects.create(
                object_id=self.page.id,
                django_content_type=DjangoContentType.objects.get_for_model(self.page),
                order=1,
                key='hero_list',
                image=self.image,
            )
            try:
                c = Context({'image': ri, 'thepage': self.page})
                t = Template('{{ image.url }}')
                self.assertEqual(t.render(c), ri.url())

                t = Template('{{ image.alt }}')
                self.assertEqual(t.render(c), ri.alt)

                t = Template('{{ image.caption }}')
                self.assertEqual(t.render(c), ri.caption)

                # Before any template access - only the non JIT one should exist.
                self.assertFalse(default_storage.exists(large_thumb))
                self.assertTrue(default_storage.exists(small_thumb))

                t = Template('{{ image.variant.small_thumb }}')
                self.assertEqual(t.render(c), 'http://localhost:8000/%s'%(small_thumb,))

                t = Template('{{ image.variant.large_thumb }}')
                self.assertEqual(t.render(c), 'http://localhost:8000/%s'%(large_thumb,))

                # After the template access - both should exist.
                self.assertTrue(default_storage.exists(large_thumb))
                self.assertTrue(default_storage.exists(small_thumb))

                # Access them as part of a page.
                t = Template('{{ thepage.image.hero.variant.small_thumb }}')
                self.assertEqual(t.render(c), 'http://localhost:8000/%s'%(small_thumb,))

                t = Template('{{ thepage.image.hero.variant.large_thumb }}')
                self.assertEqual(t.render(c), 'http://localhost:8000/%s'%(large_thumb,))

                # Access them as part of a page, list
                t = Template('{% for image in thepage.image.hero_list %}{{ image.variant.small_thumb }}{% endfor %}')
                self.assertEqual(t.render(c), 'http://localhost:8000/%s'%(small_thumb,))

                t = Template('{% for image in thepage.image.hero_list %}{{ image.variant.large_thumb }}{% endfor %}')
                self.assertEqual(t.render(c), 'http://localhost:8000/%s'%(large_thumb,))
            finally:
                ri.delete()

            # Once we delete the associated with a particular resource the variants
            # should also be deleted.
            self.assertFalse(default_storage.exists(large_thumb))
            self.assertFalse(default_storage.exists(small_thumb))

        finally:
            self.image.delete()

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class ImageVariantTests(ImageTestBase):
    def test_image_variants_defined_later_and_deleted(self):
        Image.add_image_variant(
                name="eager_crop",
                algorithm="crop",
                arguments={
                    'height': 32,
                    'width': 32,
                },
                jit_generation=False,
            )
        Image.add_image_variant(
                name="lazy_crop",
                algorithm="crop",
                arguments={
                    'height': 16,
                    'width': 16,
                },
                jit_generation=True,
            )
        self.image = Image.objects.create(
            alt='The best eagle image ever'
        )
        # Upload a test image to the Model
        self._upload_test_file(
            'content/tests/files/image.gif',
            self.image,
            'image'
        )
        try:
            lazy_crop_name = self.image.image.variant_name('lazy_crop')
            eager_crop_name = self.image.image.variant_name('eager_crop')

            self.assertFalse(
                    default_storage.exists(lazy_crop_name),
                    "The lazy cropped image shouldn't exist after save."
                )
            self.assertTrue(
                    default_storage.exists(eager_crop_name),
                    "The eager cropped image should exist after save."
                )

            lazy_crop_url = self.image.image.variant['lazy_crop']
            self.assertTrue(
                    default_storage.exists(lazy_crop_name),
                    "The lazy cropped image shouldn exist after its been accessed."
                )
            self.assertTrue(
                    default_storage.exists(eager_crop_name),
                    "The eager cropped image shouldn still exist after its the lazy access."
                )
        finally:
            self.image.delete()

        self.assertFalse(
                default_storage.exists(lazy_crop_name),
                "The lazy crop should no longer exist after delete."
            )
        self.assertFalse(
                default_storage.exists(eager_crop_name),
                "The eager crop should no longer exist after delete."
            )

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class AdminThumbTests(ImageInterfaceTests):
    def test_image_thumb_view(self):
        self.image = Image.objects.create(
            alt='The best eagle image ever'
        )
        # Upload a test image to the Model
        self._upload_test_file(
            'content/tests/files/image.gif',
            self.image,
            'image'
        )
        try:
            url = reverse(image_thumb, kwargs={"image_id":self.image.id,})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, smart_bytes(self.image.admin_thumbnail()))
        finally:
            self.image.delete()
