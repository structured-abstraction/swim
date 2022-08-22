import traceback

from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.template import Template as DjangoTemplate, Context
from django.test import override_settings
from django.utils.encoding import smart_bytes

from swim.test import TestCase, TransactionTestCase
from swim.core.models import ResourceType, Resource
from swim.design.models import ResourceTypeTemplateMapping, Image
from swim.content.models import Page
from swim.design.models import CSS, JavaScript, Template
from swim.core.validators import isValidTemplate
from swim.core import validators


#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class MediaTest(TransactionTestCase):
    def setUp(self):
        super(MediaTest, self).setUp()
        self.css1 = CSS.objects.create(
            path='css_file',
            body='.works { margin: 0; }'
        )
        self.css2 = CSS.objects.create(
            path='css_file2',
            body='.works2 { margin: 0; }'
        )
        self.js1 = JavaScript.objects.create(
            path='js_file',
            body='alert("confirmed!");'
        )
        self.js2 = JavaScript.objects.create(
            path='js_file2',
            body='alert("confirmed!2");'
        )

    def testNullAlt(self):
        image = Image(key='1', alt=None)
        image.save()

        image_new = Image.objects.get(id=image.id)
        self.assertEqual(None, image_new.alt)

        image2 = Image(key='2', alt='')
        image2.save()

        image_new2 = Image.objects.get(id=image2.id)
        self.assertEqual('', image_new2.alt)
        self.assertNotEqual(None, image_new2.alt)

        image3 = Image(key='3', alt=None)
        image3.save()


    def testMediaNamingValidator(self):
        # I know this test tests the isAlphaNumeric validator,
        # but i wanted to be certain.
        for path, allowed in (
                ('master', True),
                ('master?test', False), # question marks aren't allowed.
                ('master test', False), # spaces aren't allowed.
                ('master/test', False), # slashes aren't allowed
                ('/master', False), # slashes aren't allowed
            ):
            for model in CSS, JavaScript:
                if allowed:
                    try:
                        validators.isAlphaNumeric(path)
                    except ValidationError:
                        self.fail(
                            "path: %s is allowed for model: "
                            "%s, but resulted in errors: %s" % (
                                path, model, traceback.format_exc(),))
                else:
                    try:
                        validators.isAlphaNumeric(path)
                    except ValidationError:
                        pass # test passed as well ... get it?
                    else:
                        self.fail(
                            "path: %s is not allowed for model:"
                            " %s, but did not result in errors." % (
                                path, model,))

    def testMediaHasPriority(self):
        for model, http_content_type, url_format, object in (
                (CSS, 'text/css', '/css/%s', self.css1),
                (JavaScript, 'text/javascript', '/js/%s', self.js1),
            ):

            # CSS MUST be served up via the following URL
            response = self.client.get(url_format % object.path)
            self.assertEqual(response.status_code, 200)

            # CSS MUST be served up with the appropriate Content-type header
            self.assertTrue(
                    response.has_header('Content-type'),
                    "%s has no Content-type" % model)
            self.assertTrue(
                    response['Content-type']==http_content_type,
                    "%s Content-type is invalid" % model)

            # CSS MUST be served up with the appropriate Last-Modified header
            self.assertTrue(
                    response.has_header('Last-Modified'),
                    "%s has no Last-Modified" % model)
            self.assertTrue(
                    response['Last-Modified']==object.http_last_modified(),
                    "%s Last-Modified is incorrect" % model)
            self.assert_(
                    smart_bytes(object.body) in response.content,
                    " %s not accessible via its url." % model)


    def testCSSMultipleLoad(self):
        for model, http_content_type, url_format, object1, object2 in (
                (CSS, 'text/css', '/css/%s/%s', self.css1, self.css2),
                (JavaScript, 'text/javascript', '/js/%s/%s', self.js1, self.js2),
            ):
            response = self.client.get(url_format % (object1.path, object2.path))
            # CSS MUST be served up via the above URL
            self.assertEqual(
                    response.status_code,
                    200,
                    "%s multi-body-url is not working." % model)

            # CSS MUST have the appropriate content-type
            self.assertTrue(
                    response.has_header('Content-type'),
                    "%s has no Content-type" % model)
            self.assertTrue(
                    response['Content-type']==http_content_type,
                    "%s Content-type is invalid" % model)

            # a multi CSS MUST be served up with the appropriate Last-Modified header
            # from the object which was most recently modified.
            self.assertTrue(
                    response.has_header('Last-Modified'),
                    "%s has no Last-Modified" % model)
            self.assertTrue(
                    response['Last-Modified']==object2.http_last_modified(),
                    "%s Last-Modified is incorrect." % model)

            # All of the requested files MUST be in the response.
            self.assert_(
                    smart_bytes(object1.body) in response.content,
                    "%s not accessible via the multi url." % model)
            self.assert_(
                    smart_bytes(object2.body) in response.content,
                    "%s not accessible via the multi url." % model)

            # The request MUST maintain the same order.
            # find will return the first index where it find the value
            self.assertTrue(
                    response.content.find(smart_bytes(object1.body)) <
                    response.content.find(smart_bytes(object2.body)))

    def test404CSSMultiple(self):
        response = self.client.get('/css/%s/InVaLiD' % self.css1)
        # CSS MUST be served up via the above URL
        self.assertEqual(
            response.status_code,
            404,
            "multi-body-url where one component is invalid should 404.")
        response = self.client.get('/css/InVaLiD')
        # CSS MUST be served up via the above URL
        self.assertEqual(
                response.status_code,
                404,
                "single-body-url where one component is invalid should 404.")


    def testTemplateUniqueness(self):
        transaction.commit()
        try:
            try:
                template1 = Template.objects.create(
                    path='html',
                    body="""<h1>HTML</h1>""",
                    http_content_type="text/html; charset=utf-8",
                    swim_content_type=Resource.swim_content_type()
                )
                template2 = Template.objects.create(
                    path='html',
                    body="""Letter,Word\nH,hyper\nT,text\nM,markup\nL,language""",
                    http_content_type="text/html; charset=utf-8",
                    swim_content_type=Resource.swim_content_type()
                )
            except IntegrityError as e:
                pass
                # TODO: This error message to too sqlite3 specific.
                #expected_error = "columns path, http_content_type, swim_content_type_id are not unique"
                #self.assertTrue(
                    #expected_error in str(e),
                    #"%s doesn't contain %s" % (str(e), expected_error)
                #)
        finally:
            transaction.rollback()
        #self.assertTrue(False, "two templates can't have the same path, http_content_type, and swim_content_type")

    def testTemplateMatchingAlgorithm(self):
        index_template = Template.objects.create(
            path='/index',
            body="""Index Page""",
            swim_content_type=Resource.swim_content_type(),
            http_content_type='text/html; charset=utf-8'
        )
        about_template = Template.objects.create(
            path = '/index/about',
            body = """About Page""",
            swim_content_type=Resource.swim_content_type(),
            http_content_type='text/html; charset=utf-8'
        )
        index_type = ResourceType.objects.create(
            key='index',
            title = 'index'
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = index_type,
            template = index_template
        )
        index_content = Page.objects.create(
            path = '/index',
            resource_type = index_type,
            title = 'index',
        )
        about_type = ResourceType.objects.create(
            key='about',
            title = 'about'
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = about_type,
            template = about_template
        )
        about_content = Page.objects.create(
            path='/index/about',
            resource_type = about_type,
            title = 'about',
        )
        about_content = Page.objects.create(
            path = "/index/about/faraway",
            resource_type = about_type,
            title = 'faraway',
        )

        # The template matching MUST find the most
        # specific template it can.

        # In the case of /index/ it should be the
        # index template.
        response = self.client.get('/index')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Index Page' in response.content, "Found the wrong template!")

        # In the case of /index/about/ it should be the
        # index/about template.
        response = self.client.get('/index/about')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'About Page' in response.content, "Found the wrong template!")

        # In the case of /index/about/faraway/ it should be the
        # index/about template.
        response = self.client.get('/index/about/faraway')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'About Page' in response.content, "Found the wrong template!")

    def test_template_loading_utf8(self):
        index_template = Template.objects.create(
            path='/index',
            body="""Index Page""",
            swim_content_type=Resource.swim_content_type(),
            http_content_type='text/html; charset=utf8'
        )
        about_template = Template.objects.create(
            path = '/index/about',
            body = """{% extends "/index" %}""",
            swim_content_type=Resource.swim_content_type(),
            http_content_type='text/html; charset=utf-8'
        )
        about_type = ResourceType.objects.create(
            key='about',
            title = 'about'
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = about_type,
            template = about_template
        )
        about_content = Page.objects.create(
            path='/index/about',
            resource_type = about_type,
            title = 'about',
        )

        # The template matching MUST find the most
        # specific template it can.

        # In the case of /index/about/ it should be the
        # index/about template.
        response = self.client.get('/index/about')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Index Page' in response.content, "Found the wrong template!")


    def testTemplateMatchingAlgorithmConflict(self):
        # TODO: test that the Template Resolution order finds the template with
        # with http_content_type matching the requested page or returns an internal
        # server error if it can't
        index_template = Template.objects.create(
            path = 'index',
            body = """Index Page""",
            swim_content_type = Resource.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8',
        )
        csv_index_template = Template.objects.create(
            path = 'index',
            body = """Letter\tWord\nH\thyper\nT\ttext\nM\tmarkup\nL\tlanguage""",
            swim_content_type = Resource.swim_content_type(),
            http_content_type = 'text/tab-separated-values; charset=utf-8',
        )
        #self.assertTrue(False, "use the content type to choose between templates with the same path ")

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class TemplateFilters(TestCase):

    def test_nbsp(self):
        t = DjangoTemplate("{% load swim_utils %}{{ test|nbsp }}")

        for test_val, expected in (
                ('first second', 'first&nbsp;second'),
                ('first  second', 'first&nbsp;&nbsp;second'),
                ('first  second ', 'first&nbsp;&nbsp;second&nbsp;'),
                ('<h2>first second<h2>', '&lt;h2&gt;first&nbsp;second&lt;h2&gt;'),
                (' first second', '&nbsp;first&nbsp;second'),
            ):
            c = Context({'test':test_val})
            result = t.render(c)
            self.assertEqual(result, expected)


#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class TestValidators(TestCase):
    def test_template_validator(self):
        try:
            # We don't really need to test every potential valid template.
            # I just put a few here to test that if the template is valid,
            # the validator doesn't raise an error.
            #
            # Later, if we find that the validator is overly zealous, then
            # we can put the valid template which breaks the validator here.
            # I don't expect that to happen much because we'll use django
            # itself to validate the templates.
            isValidTemplate("{% extends \"base.html\"%}")
            isValidTemplate("{% block one %}{% endblock %}{% block two %}{% endblock %}")
        except:
            self.fail("Valid template resulted in errors: %s" %
                (traceback.format_exc(),))

        # If there are template errors, we MUST raise a ValidationError.
        # Again, we can't test all possible errors, but I'm testing the specific
        # one that got in Ian's way.
        self.assertRaises(ValidationError,
            isValidTemplate,
            "{% block one %}{% endblock %}{% block one %}{% endblock %}")
