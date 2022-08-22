from django.template import loader, TemplateDoesNotExist
from django.contrib.sites.models import Site
from django.test import override_settings
from django.utils.encoding import smart_bytes

from swim.content.tests.base import NoContentTestCase, NoTemplateTestCase
from swim.core.models import (
    ResourceType,
    ArrangementType,
    ContentSchema,
)
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.content.models import (
        Page,
        Arrangement,
        CopySlot,
    )

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class TemplateTest(NoTemplateTestCase):
    """A bundle of tests to exercise the Template models
    """

    #---------------------------------------------------------------------------
    def setUp(self):
        super(TemplateTest, self).setUp()

        self.content_schema = ContentSchema.objects.create(title='eagles')
        self.resource_type = ResourceType.objects.create(
            title = 'eagles',
            content_schema = self.content_schema,
        )
        self.page = Page.objects.create(
            path = '/eagles',
            resource_type = self.resource_type,
            title = 'eagles'
        )
        copyslot = CopySlot.objects.create(
            order = 0,
            key = 'eagle',
            content_object = self.page,
            body = 'eagles copy',
        )

    #---------------------------------------------------------------------------
    def test_path_lowering(self):
        """Test to make sure that the path store when creating a model is lower case
        """
        self.template = Template.objects.create(
            path = '/EaGlEs',
            http_content_type = 'text/html; charset=utf-8',
            body = 'This is the best eagle site ever.'
        )
        # The template MUST have a path that is all lowercase
        self.assertEqual(self.template.path, '/eagles')

    #---------------------------------------------------------------------------
    def test_empty_site_template_406(self):
        response = self.client.get('/eagles')
        self.assertEqual(response.status_code, 406)

    #---------------------------------------------------------------------------
    def test_empty_site_no_template(self):
        response = self.client.get('/eagles')
        self.assertTrue(b'no matching template was found' in response.content,
                "%s does not contain %s" % (
                    response.content, 'no matching template was found'))

    #---------------------------------------------------------------------------
    def test_eagle_site(self):
        self.template = Template.objects.create(
            path = '/eagles',
            http_content_type = 'text/html; charset=utf-8',
            body = 'This is the best eagle site ever.',
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.template
        )
        response = self.client.get('/eagles')
        self.assertEqual(response.status_code, 200)


    #---------------------------------------------------------------------------
    def test_design_templates_available_to_django(self):
        db_template = Template.objects.create(
            path = '/eagles',
            http_content_type = 'text/html; charset=utf-8',
            body = 'This is the best eagle site ever.',
        )
        try:
            template = loader.get_template('/eagles')
        except TemplateDoesNotExist:
            self.fail("Django was unable to load design template")

    #---------------------------------------------------------------------------
    def test_templates_on_various_domains(self):
        self.template = Template.objects.create(
            path = '/eagles',
            http_content_type = 'text/html; charset=utf-8',
            body = '{% load swim_tags %}Default Template. {% render resource.copy.eagle %}',
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.template
        )
        self.copy_template = Template.objects.create(
            path='/copy-template',
            body='Default Copy',
            swim_content_type=CopySlot.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8',
        )
        ResourceTypeTemplateMapping.objects.create(
            template = self.copy_template,
            resource_type = self.resource_type,
        )
        response = self.client.get('/eagles')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'Default Template. Default Copy')

        local_eagles = Site.objects.create(
                name='eagles',
                domain='local.eagles',
            )
        self.template = Template.objects.create(
            path = '/local.eagles',
            http_content_type = 'text/html; charset=utf-8',
            body = '{% load swim_tags %}Eagles Template. {% render resource.copy.eagle %}',
        )
        self.template.domains.add(local_eagles)
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.template
        )
        self.copy_template = Template.objects.create(
            path='/eagles-copy-template',
            body='Eagles Copy',
            swim_content_type=CopySlot.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8',
        )
        self.copy_template.domains.add(local_eagles)
        ResourceTypeTemplateMapping.objects.create(
            template = self.copy_template,
            resource_type = self.resource_type,
        )
        with self.settings(ALLOWED_HOSTS=['local.eagles']):
            response = self.client.get('/eagles', HTTP_HOST='local.eagles')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b'Eagles Template. Eagles Copy')

        response = self.client.get('/eagles')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'Default Template. Default Copy')


#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class ContextProcessorTests(NoContentTestCase, NoTemplateTestCase):

    def setUp(self):
        super(ContextProcessorTests, self).setUp()
        self.test_page = Page.objects.create(
            path = '/test-context',
            title = 'test page',
        )
        self.template = Template.objects.create(
            path = '/',
            body = '[{{ content.page.rss_eagle.title }}][{{ resource.title }}]'
        )
        ResourceTypeTemplateMapping.objects.create(
            template = self.template
        )

        self.arrangement_type = ArrangementType.objects.create(
            key='simple_arrangement',
            title='Simple Arrangement',
        )

    #---------------------------------------------------------------------------
    def test_page_rendering(self):

        colours = (
                'Red', 'Green', 'Blue', 'Orange', 'Yellow', 'Purple', 'Beige'
            )

        self.page = Page.objects.create(
            path = '/eagles',
            title = 'eagles'
        )
        self.template.body='{{ resource.copy.green.body }}'
        self.template.http_content_type='text/html; charset=utf-8'
        self.template.save()
        self.copy_template = Template.objects.create(
            path='/copy-template',
            body='{{ target.body }}',
            swim_content_type=CopySlot.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8',
        )
        ResourceTypeTemplateMapping.objects.create(
            template = self.copy_template
        )

        for colour in colours:
            copyslot = CopySlot.objects.create(
                order = 0,
                key = colour.lower(),
                content_object = self.page,
                body = '%s' % colour,
            )

        response = self.client.get('/eagles')
        self.assertIn(b'Green', response.content)


        # There was a bug when coding in Free And Easy Where
        # if the FIRST access to the Context object was in
        # a block, then as soon as the block was finished
        # rendering, the swim context processor generated entries
        # would be .pop()'ed off of the dict!?
        # This was because Django seems to push before it enters
        # a block and the pop afterwards.  So if we generated
        # extra context in between those messages we would lose it
        # afterwards.  This test NEEDs to continue testing that
        # behavior
        self.template.body = """
            {% load swim_tags %}{% get_resource for resource as resource %}
            {% block first %}
                {% render resource.copy.red %}
            {% endblock %}
            {% render resource.copy.green %}
            {% render resource.copy.blue %}
            {% block next %}
                {% render resource.copy.orange %}
            {% endblock %}
            {% render resource.copy.yellow %}
            {% block final %}
                {% render resource.copy.purple %}
            {% endblock %}
            {% render resource.copy.beige %}
        """
        self.template.save()
        response = self.client.get('/eagles')
        for colour in colours:
            self.assertTrue(smart_bytes(colour) in response.content,
                    "%s does not contain %s" % (
                        response.content, colour))


    #---------------------------------------------------------------------------
    def test_page_access(self):
        """
        Tests the content.page accessor.
        """
        # MUST allow for access to a page with the path: /rss/eagle from the template
        # as content.page.rss_eagle
        eagle = Page.objects.create(
            path = '/rss/eagle',
            title = 'eagle page',
        )
        self.template.body = '[{{ content.page.rss_eagle.title }}][{{ resource.title }}]'
        self.template.save()

        response = self.client.get(self.test_page.path)

        self.assertEqual(response.content, b"[eagle page][test page]")

