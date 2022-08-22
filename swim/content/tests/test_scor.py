from django.conf import settings
from django.test import override_settings
from django.utils.encoding import smart_bytes

from swim.content.tests.base import NoContentTestCase
from swim.core.models import ResourceType, ContentSchema, ArrangementType
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.content.models import (
        Arrangement,
        Copy,
        Link,
        Page,
        Menu,
        MenuLink,
        CopySlot,
        MenuSlot,
        ArrangementSlot,
    )

#-------------------------------------------------------------------------------
@override_settings(DEBUG=True, ROOT_URLCONF='swim.urls')
class SCORTest(NoContentTestCase):

    def setUp(self):
        super(SCORTest, self).setUp()

        self.csm = ContentSchema.objects.get(title = "Simple Page")
        self.arrangement_type = ArrangementType.objects.create(
            key='simple_type',
            title="Simple Type",
            content_schema=self.csm,
        )

    def tearDown(self):
        super(SCORTest, self).tearDown()

    def testRenderTag(self):
        self.page_template = Template.objects.create(
            path='/',
            body='''
                {% load swim_tags %}{% get_resource for resource as resource %}
                {% render resource.copy.green %}
            ''',
            http_content_type = 'text/html; charset=utf-8',
        )
        self.copy_template = Template.objects.create(
            path='/',
            body='{{ target.body }}',
            swim_content_type=Copy.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8',
        )
        self.content_schema = ContentSchema.objects.create(
                title = 'copyscor',
            )
        self.resource_type = ResourceType.objects.create(
                title='copyscor',
                content_schema = self.content_schema,
            )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.page_template
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.copy_template
        )
        self.page = Page.objects.create(
            resource_type = self.resource_type,
            path='/',
            title = 'test page',
        )
        self.copy = Copy.objects.create(body = 'This is green text')
        self.copy_slot = CopySlot.objects.create(
            order = 0,
            content_object = self.page,
            copy = self.copy,
            key = 'green'
        )
        response = self.client.get('/')
        self.assertIn(b'This is green text', response.content)


    def testCopySCOR(self):
        self.page_template = Template.objects.create(
            path='/',
            body=u'''
                {% load swim_tags %}{% get_resource for resource as resource %}
                {% render resource.copy.green %}
            ''',
            http_content_type = 'text/html; charset=utf-8',
        )
        self.copy_template = Template.objects.create(
            path='/',
            body='{{ target.body }}',
            swim_content_type=Copy.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8',
        )
        self.content_schema = ContentSchema.objects.create(
                title = 'copyscor',
            )
        self.resource_type = ResourceType.objects.create(
                title='copyscor',
                content_schema = self.content_schema,
            )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.page_template
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.copy_template
        )
        self.page = Page.objects.create(
            resource_type = self.resource_type,
            path='/',
            title = 'test page',
        )
        self.copy = Copy.objects.create(body = 'This is green text')
        self.copy_slot = CopySlot.objects.create(
            order = 0,
            content_object = self.page,
            copy = self.copy,
            key = 'green'
        )
        response = self.client.get('/')
        self.assertIn(b'This is green text', response.content)

    def testMenuSCOR(self):
        self.page_template = Template.objects.create(
            path = '/',
            body='''
                {% load swim_tags %}{% render resource.menu.index %}
            ''',
            http_content_type = 'text/html; charset=utf-8',
        )
        self.menu_template = Template.objects.create(
            path = '/',
            body="""
                {{ target.title }}
                {% for item in target.links %}
                    {{ item.url }}
                {% endfor %}
                {{ target.title }}
                """,
            swim_content_type=Menu.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8',
        )
        self.content_schema = ContentSchema.objects.create(title='menuscor')
        self.resource_type = ResourceType.objects.create(
                title='menuscor',
                content_schema = self.content_schema,
            )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.page_template
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.menu_template
        )
        self.page = Page.objects.create(
            resource_type = self.resource_type,
            path = '/eagles',
            title = 'The eagle page',
        )
        self.menu = Menu.objects.create(
            title = "Title",
        )
        MenuSlot.objects.create(
                order = 0,
                key = 'index',
                content_object = self.page,
                menu = self.menu,
            )
        self.link = Link.objects.create(
            url = 'http://www.google.com/',
            title = 'The best site ever'
        )
        self.menulink = MenuLink.objects.create(
            menu = self.menu,
            order = 1,
            link = self.link
        )

        response = self.client.get('/eagles')

        # The result MUST contain http://www.google.com/
        self.assertTrue(b'http://www.google.com/' in response.content,
                "%s does not contain %s" % (
                    response.content, 'http://www.google.com/'))
        # The result MUST contain 'The eagle list' twice in it's output
        self.assertEqual(
                response.content.count(smart_bytes(self.menu.title)), 2,
                "The menu title was not displayed twice")

    def testMenuSCOR_Defaults(self):
        self.page_template = Template.objects.create(
            path = '/',
            body='''
                {% load swim_tags %}{% render resource.menu.index %}
            ''',
            http_content_type = 'text/html; charset=utf-8',
        )
        self.menu_template = Template.objects.create(
            path = '/',
            body="""
                {{ target.title }}
                {% for item in target.links %}
                    {{ item.url }}
                {% endfor %}
                {{ target.title }}
                """,
            swim_content_type=Menu.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8',
        )
        ResourceTypeTemplateMapping.objects.create(
            order = 0,
            template = self.page_template
        )
        ResourceTypeTemplateMapping.objects.create(
            order = 0,
            template = self.menu_template,
        )
        self.page = Page.objects.create(
            path = '/eagles',
            title = 'The eagle page',
        )
        self.menu = Menu.objects.create(title='Index')
        MenuSlot.objects.create(
                order = 0,
                key = 'index',
                content_object = self.page,
                menu = self.menu,
            )
        self.link = Link.objects.create(
            url = 'http://www.google.com/',
            title = 'The best site ever'
        )
        self.menulink = MenuLink.objects.create(
            menu = self.menu,
            order = 1,
            link = self.link
        )

        response = self.client.get('/eagles')

        # The result MUST contain http://www.google.com/
        self.assertTrue(b'http://www.google.com/' in response.content,
                "%s does not contain %s" % (
                    response.content, 'http://www.google.com/'))
        # The result MUST contain 'The eagle list' twice in it's output
        self.assertEqual(
                response.content.count(smart_bytes(self.menu.title)), 2,
                "The menu title was not displayed twice")

    def testArrangementSCOR(self):
        self.page_template = Template.objects.create(
            path = '/',
            body='''
                {% load swim_tags %}{% get_resource for resource as resource %}
                {% render resource.arrangement.yellow %}
            ''',
            http_content_type = 'text/html; charset=utf-8'
        )
        self.arrangement_template = Template.objects.create(
            path = '/',
            body="""
                    arrangement-{{ target.id }}
                    {{ target.copy.green1.body }}
                    arrangement-{{ target.id }}
                     """,
            swim_content_type=Arrangement.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8'
        )
        self.content_schema = ContentSchema.objects.create(
                title = 'copyscor',
            )
        self.resource_type = ResourceType.objects.create(
                title='copyscor',
                content_schema = self.content_schema,
            )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.arrangement_template
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.page_template
        )
        self.page = Page.objects.create(
            resource_type = self.resource_type,
            path = '/eagles',
            title = 'The eagle page',
        )
        self.arrangement = Arrangement.objects.create(
                arrangement_type = self.arrangement_type
            )
        self.copy = Copy.objects.create(
            body = 'http://www.google.com/'
        )
        self.arrangement_copy = CopySlot.objects.create(
            order = 1,
            key = 'green1',
            content_object = self.arrangement,
            copy = self.copy
        )
        self.pagearrangement = ArrangementSlot.objects.create(
            order = 1,
            content_object = self.page,
            arrangement = self.arrangement,
            key = 'yellow'
        )

        response = self.client.get('/eagles')

        # The result MUST contain http://www.google.com/
        self.assertIn(b'http://www.google.com/', response.content)
        # The result MUST contain 'The eagle list' twice in it's output
        self.assertEqual(
                response.content.count(smart_bytes("arrangement-%s" % self.arrangement.id)),
                2,
                "'%s' was not displayed twice: %s" % ("arrangement-%s" % self.arrangement.id, response.content)
            )

    def testArrangementSCORKeyBasedAccess(self):
        self.page_template = Template.objects.create(
            path = '/',
            body='''
                {% load swim_tags %}{% get_resource for resource as resource %}
                {% render resource.arrangement.yellow %}
            ''',
            http_content_type = 'text/html; charset=utf-8'
        )
        self.arrangement_template = Template.objects.create(
            path = '/',
            body="""
                    {% load swim_tags %}arrangement-{{ target.id }}
                    {% render target.copy.orange %}
                    {{ target.copy.orange.body }}
                    arrangement-{{ target.id }}
                     """,
            swim_content_type=Arrangement.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8'
        )
        self.content_schema = ContentSchema.objects.create(
                title = 'copyscor',
            )
        self.resource_type = ResourceType.objects.create(
                title='copyscor',
                content_schema = self.content_schema,
            )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.arrangement_template
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.page_template
        )
        self.page = Page.objects.create(
            resource_type = self.resource_type,
            path = '/eagles',
            title = 'The eagle page',
        )
        self.arrangement = Arrangement.objects.create(
                arrangement_type = self.arrangement_type
            )
        self.copy = Copy.objects.create(
            body = 'http://www.google.com/'
        )
        self.arrangement_copy = CopySlot.objects.create(
            order = 1,
            key = 'orange',
            content_object = self.arrangement,
            copy = self.copy
        )
        self.pagearrangement = ArrangementSlot.objects.create(
            order = 1,
            content_object = self.page,
            arrangement = self.arrangement,
            key = 'yellow'
        )

        response = self.client.get('/eagles')

        # The result MUST contain http://www.google.com/
        self.assertIn(b'http://www.google.com/', response.content)
        # The result MUST contain 'The eagle list' twice in it's output
        self.assertEqual(
                response.content.count(smart_bytes("arrangement-%s" % self.arrangement.id)),
                2,
                "'%s' was not displayed twice: %s" % ("arrangement-%s" % self.arrangement.id, response.content)
            )

        # Even in the case where we don't loop, but explicitly just output
        # the key - we should get the same output.
        self.arrangement_template.body = """
                    {% load swim_tags %}arrangement-{{ target.id }}
                    {% render target.copy.orange %}
                    arrangement-{{ target.id }}
                     """
        self.arrangement_template.save()


        response = self.client.get('/eagles')

        # The result MUST contain http://www.google.com/
        self.assertIn(b'http://www.google.com/', response.content)
        # The result MUST contain 'The eagle list' twice in it's output
        self.assertEqual(
                response.content.count(smart_bytes("arrangement-%s" % self.arrangement.id)),
                2,
                "'%s' was not displayed twice: %s" % ("arrangement-%s" % self.arrangement.id, response.content)
            )

    def test_rendering_uses_resource_type_sco_before_it_uses_model_sco(self):
        self.resource_template = Template.objects.create(
            path='/',
            body='''{% load swim_tags %}{% get_resource for resource as resource %}{% render resource %}''',
            http_content_type = 'text/html; charset=utf-8',
        )
        self.page_template = Template.objects.create(
            path='/',
            body='PAGE',
            swim_content_type=Page.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8',
        )
        self.resource_type = ResourceType.objects.get(key = 'simple_page')
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.resource_template
        )
        self.page_rtt = ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.page_template
        )
        self.page = Page.objects.create(
            resource_type = self.resource_type,
            path='/',
            title = 'test page',
        )

        # In this case the only template we have registered is registered based on
        # the Page models' swim_content_type so it MUST use that template
        response = self.client.get('/')
        self.assertEqual(b'PAGE', response.content)
        self.simple_page_template = Template.objects.create(
            path = '/simple_page',
            body = 'SIMPLE PAGE',
            swim_content_type = self.resource_type.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8',
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.simple_page_template,
        )

        # In this case we have two potential templates:
        # the template registerd for the Page models' swim_content_type
        # AND the template registered for the simple_page ResourceType so
        # in this case it MUST prefer the simple page template
        response = self.client.get('/')
        self.assertEqual(b'SIMPLE PAGE', response.content)

        self.page_rtt.delete()
        # In this case the only template is the template registered for
        # the simple_page ResourceType so
        # in this case it MUST use the simple page template
        response = self.client.get('/')
        self.assertEqual(b'SIMPLE PAGE', response.content)
