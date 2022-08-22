from swim.test import TestCase
from swim.core.models import (
    ResourceType,
    ContentSchema,
)
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.content.models import Page
from django.test import override_settings


#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class AcceptHeaderTests(TestCase):
    """A suite of tests for exercising the the Accept Header parsing.
    """

    #---------------------------------------------------------------------------
    def test_accept_header_chooses_output_type(self):
        content_schema = ContentSchema.objects.create(title="Eagles")
        resource_type = ResourceType.objects.create(
            title = 'eagles',
            content_schema = content_schema,
        )
        page = Page.objects.create(
            path = '/eagles',
            resource_type = resource_type,
            title = 'eagles'
        )
        html_template = Template.objects.create(
            path = '/eagles/html',
            http_content_type = 'text/html; charset=utf-8',
            body = 'HTML',
        )
        json_template = Template.objects.create(
            path = '/eagles/json',
            http_content_type = 'application/json',
            body = '["JSON"]',
        )
        ResourceTypeTemplateMapping.objects.create(
            order = 1,
            resource_type = resource_type,
            template = html_template
        )
        ResourceTypeTemplateMapping.objects.create(
            order = 2,
            resource_type = resource_type,
            template = json_template
        )

        # Test that the appropriate templates are chosen to render the resource
        # based on the http_content_type value on the template AND the incoming
        # Accept Header
        default_error_msg = b"Your client sent this Accept header: %s. But no "\
                b"matching template was found that can produce these types. This "\
                b"resource only emits these media types: text/html, application/json."
        test_cases = (
            # (headers, status, expected_body)
            ({}, 200, b'HTML'),
            ({'HTTP_ACCEPT': '*/*'}, 200, b'HTML'),
            ({'HTTP_ACCEPT': 'text/html'}, 200, b'HTML'),
            ({'HTTP_ACCEPT': 'text/*'}, 200, b'HTML'),
            ({'HTTP_ACCEPT': 'application/json'}, 200, b'["JSON"]'),
            ({'HTTP_ACCEPT': 'application/*'}, 200, b'["JSON"]'),
            ({'HTTP_ACCEPT': 'app/doesnt_exist'}, 406, default_error_msg % b'app/doesnt_exist'),
            ({'HTTP_ACCEPT': 'nope/*'}, 406, default_error_msg % b'nope/*'),
        )

        for headers, status, expected_body in test_cases:
            response = self.client.get('/eagles', **headers)
            self.assertEqual(response.status_code, status)
            self.assertEqual(expected_body, response.content)


