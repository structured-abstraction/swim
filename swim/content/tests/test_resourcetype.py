from django.conf import settings
from django.test import override_settings

from swim.test import TestCase
from swim.core.models import (
    ContentSchema,
    Resource,
    ResourceType,
    ResourceTypeMiddleware,
    ResourceTypeMiddlewareMapping,
)
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.content.models import (
        Page,
    )
from swim.core.management import register_swim_middleware



#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class ResourceTypeMiddlewareTest(TestCase):
    """A suite of tests for exercising the ResourceTypeMiddleware system
    """

    #---------------------------------------------------------------------------
    def setUp(self):
        super(ResourceTypeMiddlewareTest, self).setUp()
        self.settings = settings.SWIM_MIDDLEWARE_MODULES
        settings.SWIM_MIDDLEWARE_MODULES += (
            'swim.content.tests.files.swimmiddleware',
        )

        # This call should really be tested, rather than just
        # assumed to work...
        register_swim_middleware()

        # Create some test pages for each test.
        self.page = Page.objects.create(
            path = '/middleware',
            title = 'middleware'
        )
        self.template = Template.objects.create(
            path = '/middleware',
            http_content_type = 'text/html; charset=utf-8',
            body = 'This content should not be returned',
            swim_content_type = Resource.swim_content_type(),
        )
        ResourceTypeTemplateMapping.objects.create(
            template = self.template
        )

    #---------------------------------------------------------------------------
    def tearDown(self):
        settings.SWIM_MIDDLEWARE_MODULES = self.settings

    #---------------------------------------------------------------------------
    def testErrorOnMissingModule(self):
        settings.SWIM_MIDDLEWARE_MODULES = (
            'swim.fake.middleware',
        )

        try:
            register_swim_middleware()
            self.fail('register_swim_middleware did not throw an exception given a missing module')
        except ImportError as e:
            pass

    #---------------------------------------------------------------------------
    def testAddContext(self):
        self.function = ResourceTypeMiddleware.objects.get(
            function = 'swim.content.tests.files.swimmiddleware.add_to_context'
        )
        self.code = ResourceTypeMiddlewareMapping.objects.create(
            function = self.function
        )

        response = self.client.get('/middleware')
        context = response.context
        if isinstance(response.context, (tuple, list)):
            context = context[0]
        self.assertEqual(context['key'], "What the hell.")

    #---------------------------------------------------------------------------
    def testRaise404(self):
        self.function = ResourceTypeMiddleware.objects.get(
            function = 'swim.content.tests.files.swimmiddleware.return_404'
        )
        self.code = ResourceTypeMiddlewareMapping.objects.create(
            function = self.function
        )

        response = self.client.get('/middleware')
        self.assertEqual(404, response.status_code)

    #---------------------------------------------------------------------------
    def testCause500(self):
        self.function = ResourceTypeMiddleware.objects.get(
            function = 'swim.content.tests.files.swimmiddleware.cause_500'
        )
        self.code = ResourceTypeMiddlewareMapping.objects.create(
            function = self.function
        )

        # The response MUST be a 500
        try:
            response = self.client.get('/middleware')
        except Exception as e:
            pass # This request should throw an exception
        else:
            self.fail("Response failed to throw an exception")

    #---------------------------------------------------------------------------
    def testInheritedMiddleware(self):
        self.content_schema = ContentSchema.objects.create(title='Parent')
        self.resource_type = ResourceType.objects.create(
                key = 'parent',
                parent = None,
                title = 'Parent',
                content_schema = self.content_schema,
            )
        self.child_type = ResourceType.objects.create(
                parent = self.resource_type,
                title = 'Child',
                content_schema = self.content_schema,
            )
        self.function = ResourceTypeMiddleware.objects.get(
            function = 'swim.content.tests.files.swimmiddleware.add_to_context'
        )
        code = ResourceTypeMiddlewareMapping.objects.create(
            resource_type = self.resource_type,
            function = self.function
        )

        # Create some test pages for each test.
        page = Page.objects.create(
            path = '/child',
            resource_type = self.child_type,
            title = 'middleware'
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.template
        )

        # Even tho the child resource_type doesn't have the middleware registered,
        # the parent resource_type does, and so the middleware should run.
        response = self.client.get('/child')
        self.assertEqual(response.context['key'], "What the hell.")

    #---------------------------------------------------------------------------
    def testInheritedTemplates(self):
        self.content_schema = ContentSchema.objects.create(title='Parent')
        self.resource_type = ResourceType.objects.create(
                key = 'parent',
                parent = None,
                title = 'Parent',
                content_schema = self.content_schema,
            )
        self.child_type = ResourceType.objects.create(
                key='child',
                parent = self.resource_type,
                title = 'Child',
                content_schema = self.content_schema,
            )
        self.child_with_template_type = ResourceType.objects.create(
                key='child_with_template',
                parent = self.resource_type,
                title = 'Child With Template',
                content_schema = self.content_schema,
            )

        # Create some test pages for each test.
        page = Page.objects.create(
            path = '/parent',
            resource_type = self.resource_type,
            title = 'middleware'
        )
        # Create some test pages for each test.
        page = Page.objects.create(
            path = '/child',
            resource_type = self.child_type,
            title = 'middleware'
        )
        # Create some test pages for each test.
        page = Page.objects.create(
            path = '/child-with-template',
            resource_type = self.child_with_template_type,
            title = 'middleware'
        )

        # Create some templates.
        parent_template = Template.objects.create(
            path = '/parent',
            http_content_type = 'text/html; charset=utf-8',
            body = 'parent',
            swim_content_type = Resource.swim_content_type(),
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = parent_template,
        )
        # Create some templates.
        child_template = Template.objects.create(
            path = '/child',
            http_content_type = 'text/html; charset=utf-8',
            body = 'child',
            swim_content_type = Resource.swim_content_type(),
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.child_with_template_type,
            template = child_template,
        )

        # The parent template should be used on the parent page
        # Because they are directly mapped.
        response = self.client.get('/parent')
        self.assertEqual(response.content, b"parent")

        # The child template should be used on the child-with-template page
        # Because they are directly mapped.
        response = self.client.get('/child-with-template')
        self.assertEqual(response.content, b"child")

        # The parent template should be used on the child page
        # Because it doesn't have a template directly mapped so it should
        # fall back to the parent template.
        response = self.client.get('/child')
        self.assertEqual(response.content, b"parent")


