from swim.content.tests.base import NoContentTestCase, NoTemplateTestCase
from swim.core.models import (
    ArrangementType,
    ContentSchema,
    ContentSchemaMember,
)
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.content.models import (
        Copy,
        Page,
        Arrangement,
        CopySlot,
        ArrangementSlot,
        PageSlot,
    )
from django.test import override_settings

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class ContentAccessorTests(NoContentTestCase, NoTemplateTestCase):

    def setUp(self):
        super(ContentAccessorTests, self).setUp()
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
    def test_content_accessor(self):
        copy_accessor = self.test_page.copy

        # Before any copy has been associated with self.test_page
        # all accesses should raise Copy.DoesNotExist
        try:
            copy_accessor['title']
            self.fail("Access to non-existant keys MUST raise a KeyError")
        except KeyError:
            pass

        # Associate a piece of copy with the test_page at that key.
        copy = Copy.objects.create(
            body='This is the test text'
        )
        copyslot = CopySlot.objects.create(
            order=0,
            key='title',
            content_object=self.test_page,
            copy=copy
        )

        # We will have cached the results at this point, so we'll
        # need to get a new instance of the class in order to get the new data.
        self.test_page = Page.objects.get(pk=self.test_page.id)
        copy_accessor = self.test_page.copy
        copy_list = copy_accessor['title']
        self.assertEqual(copy, copy_list)

        copyslot.delete()
        copy.delete()


    #---------------------------------------------------------------------------
    def test_resource_lists(self):
        self.copy = Copy.objects.create(
            body = 'This is the test text'
        )
        self.page = Page.objects.create(
            path = '/',
            title = 'eagles',
        )
        for i in range(3):
            self.copyslot = CopySlot.objects.create(
                order = i,
                key = 'green',
                content_object = self.page,
                copy = self.copy
            )
        ContentSchemaMember.objects.create(
                content_schema = ContentSchema.objects.get(title='default'),
                order=1,
                key='green',
                title='Green!',
                cardinality = 'list',
                swim_content_type = Copy.swim_content_type(),
            )
        self.copy_template = Template.objects.create(
            path='/copy-template',
            body='{{ target.body }}',
            swim_content_type=Copy.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8',
        )
        ResourceTypeTemplateMapping.objects.create(
            template = self.copy_template
        )

        # Iteration over the list should work!
        self.template.body = '''
                {% load swim_tags %}{% get_resource for resource as resource %}
                {% for copy in resource.copy.green %}{% render copy %}{% endfor %}
            '''
        self.template.http_content_type = 'text/html; charset=utf-8'
        self.template.save()

        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
        self.assertCount(3, b'This is the test text', response.content)

        # Single access should act like a simple iteration
        self.template.body = '''
            {% load swim_tags %}{% get_resource for resource as resource %}
            {% render resource.copy.green %}
        '''
        self.template.save()
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
        self.assertCount(3, b'This is the test text', response.content)

    #---------------------------------------------------------------------------
    def test_copy_access(self):
        self.copy = Copy.objects.create(
            body = 'This is the test text'
        )
        self.copyslot = CopySlot.objects.create(
            order = 0,
            key = 'green',
            content_object = self.test_page,
            copy = self.copy
        )
        self.template.body = '{{ resource.copy.green.body }}'
        self.template.http_content_type = 'text/html; charset=utf-8'
        self.template.save()
        response = self.client.get(self.test_page.path)
        self.assertEqual(200, response.status_code)
        self.assertIn(b'This is the test text', response.content)


    #---------------------------------------------------------------------------
    def test_arrangement_access(self):
        # First go around try to access a copy object associated with
        # an arrangement that's associated with a page.
        self.arrangement = Arrangement.objects.create(
                arrangement_type=self.arrangement_type,
            )
        self.copy = Copy.objects.create(
            body = 'This is the test text'
        )
        self.copyslot = CopySlot.objects.create(
            order = 0,
            key = 'green',
            content_object = self.arrangement,
            copy = self.copy
        )
        self.arrangementslot = ArrangementSlot.objects.create(
            order=0,
            key='grapes',
            content_object=self.test_page,
            arrangement=self.arrangement,
        )
        self.template.body = '{{ resource.arrangement.grapes.copy.green.body }}'
        self.template.http_content_type = 'text/html; charset=utf-8'
        self.template.save()

        response = self.client.get(self.test_page.path)
        self.assertEqual(200, response.status_code)
        self.assertIn(b'This is the test text', response.content)

        # Second go around access the copy associated with an arrangement
        # that's nested inside an arrangement that's associated with a page.
        self.second_arrangement = Arrangement.objects.create(
                arrangement_type=self.arrangement_type,
            )
        self.arrangementslot = ArrangementSlot.objects.create(
            order=0,
            key='apples',
            content_object=self.arrangement,
            arrangement=self.second_arrangement,
        )
        self.copy = Copy.objects.create(
            body = 'Some more rand0m text!'
        )
        self.copyslot = CopySlot.objects.create(
            order = 0,
            key = 'random',
            content_object = self.second_arrangement,
            copy = self.copy
        )
        self.template.body = '{{ resource.arrangement.grapes.arrangement.apples.copy.random.body }}'
        self.template.http_content_type = 'text/html; charset=utf-8'
        self.template.save()

        response = self.client.get(self.test_page.path)
        self.assertEqual(200, response.status_code)
        self.assertIn(b'Some more rand0m text!', response.content)

    #---------------------------------------------------------------------------
    #def test_page_access(self):
        #self.assertEqual(1, 2)
        #self.copy = Copy.objects.create(
            #body = 'This is the test text'
        #)
        #self.copyslot = CopySlot.objects.create(
            #order = 0,
            #key = 'green',
            #content_object = self.test_page,
            #copy = self.copy
        #)
        #self.template.body = '{{ resource.copy.green.body }}'
        #self.template.http_content_type = 'text/html; charset=utf-8'
        #self.template.save()
        #response = self.client.get(self.test_page.path)
        #self.assertEqual(200, response.status_code)
        #self.assertIn(b'This is the test text', response.content)

