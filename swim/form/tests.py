from django.conf import settings
from django import forms
from django.test import override_settings
from django.utils.encoding import smart_bytes

from swim.test import TestCase
from swim.core.models import ResourceType, Resource
from swim.content.models import (
    Page,
)
from swim.design.models import ResourceTypeTemplateMapping, Template
from swim.form.models import (
    FormFieldArrangement,
    FormField,
    Form,
    FormHandler,
    FormFieldType,
    FormFieldConstructor,
    FormFieldValidator,
    FormValidator
)
from swim.form.management import register_swim_form_handler

#-------------------------------------------------------------------------------
def onlyDigits(value):
    import string
    for x in value:
        if x not in string.digits:
            raise forms.ValidationError("'%s' contains more than digits")

    return value

#-------------------------------------------------------------------------------
def validateForm(form, cleaned_data):
    raise forms.ValidationError("Form Doesnt Validate!")


#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class FormTest(TestCase):
    """A suite of tests for exercising the swim.form module
    """

    #---------------------------------------------------------------------------
    def setUp(self):
        super(FormTest, self).setUp()

        # Create some test pages / content
        self.test_path = '/test'
        self.page1 = Page.objects.create(
            path = self.test_path,
            title = 'test page'
        )
        self.page2 = Page.objects.create(
            path = '/success',
            title = 'test page'
        )
        self.template = Template.objects.create(
            path = self.test_path,
            http_content_type = 'text/html; charset=utf-8',
            body = '''
                {% load swim_tags %}{% render content.form.green %}
                {% render content.form.search %}
                ''',
            swim_content_type = Resource.swim_content_type()
        )
        ResourceTypeTemplateMapping.objects.create(
            order = 0, # Move it above the default
            template = self.template
        )
        self.formfieldarrangement = FormFieldArrangement.objects.create(
            name = 'contact form'
        )
        self.formfield = FormField.objects.create(
            form = self.formfieldarrangement,
            name = 'username',
            label = 'Username:',
            help_text = 'Some help text',
            order = 1,
            type = FormFieldType.objects.get(name = 'text'),
            required = True
        )
        self.searchfieldarrangement = FormFieldArrangement.objects.create(
            name = 'search form'
        )
        self.formfield = FormField.objects.create(
            form = self.searchfieldarrangement,
            name = 'search',
            label = 'Search:',
            help_text = 'Some help text',
            order = 1,
            type = FormFieldType.objects.get(name = 'text'),
            required = True
        )

        self.formvalidator = FormValidator.objects.create(
                title='Validate Form',
                function='swim.form.tests.validateForm',
            )

        # Register some test form handlers.
        self.settings = settings.SWIM_FORM_HANDLER_MODULES
        settings.SWIM_FORM_HANDLER_MODULES = (
            'swim.form.test_files.swimformhandler',
        )

        register_swim_form_handler()

    #---------------------------------------------------------------------------
    def tearDown(self):
        settings.SWIM_FORM_HANDLER_MODULES = self.settings

    #---------------------------------------------------------------------------
    def testPostingToAUrlThatHasNoForm(self):
        # Posting data to a URL that has no form MUST return a 405 response
        response = self.client.post(self.test_path, {'username' : ''})
        self.assertEquals(response.status_code, 405)
        self.assertTrue(response.has_header('Allow'))
        self.assertTrue('GET' in response['Allow'])
        self.assertTrue('POST' not in response['Allow'])

    #---------------------------------------------------------------------------
    def testGettingAUrlThatOnlyHasAForm(self):
        self.handler = FormHandler.objects.get(
            function = 'swim.form.test_files.swimformhandler.foo'
        )
        # Requesting a GET from a URL that only has a form defined on it must
        # return a 405.
        self.form = Form.objects.create(
            key = 'test',
            name = 'testform',
            action = '/test/get/405',
            success_url = '/success',
            handler = self.handler,
            form_fields = self.formfieldarrangement
        )

        response = self.client.get('/test/get/405')
        self.assertEqual(response.status_code, 405);
        self.assertTrue(response.has_header('Allow'))
        self.assertTrue('POST' in response['Allow'])
        self.assertTrue('GET' not in response['Allow'])

    #---------------------------------------------------------------------------
    def testErrorRedirectAndDisplay(self):
        self.handler = FormHandler.objects.get(
            function = 'swim.form.test_files.swimformhandler.foo'
        )
        self.form = Form.objects.create(
            key = 'green',
            name = 'contact',
            action = self.test_path,
            success_url = '/success',
            handler = self.handler,
            form_fields = self.formfieldarrangement
        )
        self.searchform = Form.objects.create(
            key = 'search',
            name = 'search',
            action = '/search',
            success_url = '/search',
            handler = self.handler,
            form_fields = self.searchfieldarrangement,
        )

        # Requesting the self.test_path page should display the form without errors
        response = self.client.get(self.test_path)
        self.assertFalse(b'This field is required.' in response.content)

        # POST'n empty data, causes the server to redirect to self.test_path and then
        # display the form with an error
        response = self.client.post(self.test_path, {'username' : ''})
        self.assertEquals(response.status_code, 302)

        response = self.client.get(self.test_path)
        # Even though there are two forms in the rendering ONLY one of them
        # should have the error message.
        self.assertCount(1, b'This field is required', response.content)

    #---------------------------------------------------------------------------
    def testSuccessAndRedirect(self):
        self.handler = FormHandler.objects.get(
            function = 'swim.form.test_files.swimformhandler.foo'
        )
        self.form = Form.objects.create(
            key = 'green',
            name = 'contact',
            action = self.test_path,
            success_url = self.test_path,
            handler = self.handler,
            form_fields = self.formfieldarrangement
        )

        # POST'n correct data should cause the server to respond with a
        # redirect to the success page.
        response = self.client.post(self.test_path, {'username' : 'hair'})
        self.assertRedirects(response, self.test_path)

        # The foo handler MUST have created a new page under the path:
        # /new/page
        try:
            Page.objects.get(path = '/new/page')
        except Page.DoesNotExist as e:
            self.fail('/new/page was not created')

    #---------------------------------------------------------------------------
    def testFormFieldSCOR(self):
        self.handler = FormHandler.objects.get(
            function = 'swim.form.test_files.swimformhandler.foo'
        )
        self.form = Form.objects.create(
            key = 'green',
            name = 'contact',
            action = self.test_path,
            success_url = self.test_path,
            handler = self.handler,
            form_fields = self.formfieldarrangement
        )
        self.field_template = Template.objects.create(
            path = '/system/default/textfield',
            http_content_type = 'text/html; charset=utf-8',
            body = 'BUBBLES',
            swim_content_type = FormFieldType.objects.get(name = 'text').swim_content_type
        )
        self.field_template_type = ResourceTypeTemplateMapping.objects.create(
                template = self.field_template,
            )
        self.form_template = Template.objects.get(path='/system/default/form')
        self.form_template.body = """
            {% load swim_tags %}{% for field in target.field_list %}
                {% render field %}
            {% endfor %}
        """
        self.form_template.save()

        # The response MUST contain 'BUBBLES' which is the SCOT for
        # text form fields.
        response = self.client.get(self.test_path)
        self.assertIn(b'BUBBLES', response.content)

    #---------------------------------------------------------------------------
    def testFormFieldRendering(self):
        """
        Test that the default rendering for the form fields is appreopriate.
        """
        self.handler = FormHandler.objects.get(
            function = 'swim.form.test_files.swimformhandler.foo'
        )
        renderingarrangement = FormFieldArrangement.objects.create(
            name = 'TestRendering Form'
        )
        test_cases = (
                ('text', 'Text:', 'Help Text',
                    FormFieldType.objects.get(name='text'), False, "<input type=\"text\" name=\"text\" id=\"id_text\""),

                ('textarea', 'Textarea:', 'Help Text',
                    FormFieldType.objects.get(name='textarea'), False, "<textarea "),
                ('checkbox', 'Checkbox:', 'Help Text',
                    FormFieldType.objects.get(name='checkbox'), False, "<input type=\"checkbox\" name=\"checkbox\" id=\"id_checkbox\""),
                ('image', 'Image:', 'Help Text',
                    FormFieldType.objects.get(name='image'), False, "<input type=\"file\" name=\"image\" id=\"id_image\""),
                ('file', 'File:', 'Help Text',
                    FormFieldType.objects.get(name='file'), False, "<input type=\"file\" name=\"file\" id=\"id_file\""),
                ('password', 'Password:', 'Help Text',
                    FormFieldType.objects.get(name='password'), False, "<input type=\"password\" name=\"password\" id=\"id_password\""),
                ('hidden', 'Hidden:', 'Help Text',
                    FormFieldType.objects.get(name='hidden'), False, "<input type=\"hidden\" name=\"hidden\" id=\"id_hidden\""),
            )
        for i, (name, label, help_text, type, required, _) in enumerate(test_cases):
            formfield = FormField.objects.create(
                form = renderingarrangement,
                name = name,
                label = label,
                help_text = help_text,
                order = i,
                type = type,
                required = required
            )

        self.form = Form.objects.create(
            key = 'green',
            name = 'test_rendering',
            action = self.test_path,
            success_url = self.test_path,
            handler = self.handler,
            form_fields = renderingarrangement
        )
        self.form_template = Template.objects.get(path='/system/default/form')
        self.form_template.body = """
            {% for field in target.field_list %}
                {{ field.django_field }}
            {% endfor %}
        """
        self.form_template.save()

        # The response MUST contain the expected default input types fore each widget.
        response = self.client.get(self.test_path)
        for i, (_, _, _, _, _, expected) in enumerate(test_cases):
            self.assertContains(response, expected)


    #---------------------------------------------------------------------------
    def testCustomFormFieldValidation(self):
        """
        Test that the default rendering for the form fields is appreopriate.
        """
        # Create an onlyDigits field
        email_field = FormFieldType.objects.create(
            name = 'onlyDigits',
            constructor = FormFieldConstructor.objects.get(
                function = 'swim.form.constructor.textfield'
            ),
            validator = FormFieldValidator.objects.create(
                title='onlyDigits',
                function = 'swim.form.tests.onlyDigits'
            )
        )
        type = FormFieldType.objects.get(name='onlyDigits')

        error_message = 'contains more than digits'
        self._testFormFieldValidation(
                type,
                valid_input_objects = ('12345', '1', '2', '232323'),
                invalid_input_objects = (
                    ('adf', error_message),
                    ('foo', error_message),
                    ('123a', error_message),
                    ('a1', error_message),
                )
            )


    #---------------------------------------------------------------------------
    def _testFormFieldValidation(self, field_type, valid_input_objects, invalid_input_objects):
        """
        Test that the default rendering for the form fields is appreopriate.
        """
        self.handler = FormHandler.objects.get(
            function = 'swim.form.test_files.swimformhandler.donothing'
        )
        renderingarrangement = FormFieldArrangement.objects.create(
            name = 'TestRendering Form'
        )
        formfield = FormField.objects.create(
            form = renderingarrangement,
            name = 'testField',
            label = 'testLable',
            help_text = 'test Help Text',
            order = 1,
            type = field_type,
            required = True
        )
        self.form = Form.objects.create(
            key = 'green',
            name = 'test_rendering',
            action = self.test_path,
            success_url = '/success',
            handler = self.handler,
            form_fields = renderingarrangement
        )

        for invalid_input, expected_message in invalid_input_objects:
            response = self.client.post(self.test_path, {'testField' : invalid_input})
            self.assertEqual(response.status_code, 302)

            response = self.client.get(self.test_path)
            self.assertTrue(
                smart_bytes(expected_message) in response.content,
                "Expected error message: [%s] not found in response body: %s" % (
                    expected_message,
                    response.content)
            )

        for valid_input in valid_input_objects:
            response = self.client.post(self.test_path, {'testField' : valid_input})
            self.assertRedirects(response, '/success')


    #---------------------------------------------------------------------------
    def testEmailFieldValidation(self):
        type = FormFieldType.objects.get(name='email')

        error_message = 'Enter a valid email address'
        self._testFormFieldValidation(
                type,
                valid_input_objects = (
                    'l@foo.com',
                    'example@example.com',
                    'example@example2.com',
                    'example-123@foo.subdomain.x.com.com',
                ),
                invalid_input_objects = (
                    ('adf', error_message),
                    ('asdfa@asdf', error_message),
                    ('asdfa.com', error_message),
                    ('foo@', error_message),
                )
            )

    #---------------------------------------------------------------------------
    def testFormValidation(self):
        """
        Test that the default rendering for the form fields is appreopriate.
        """
        self.handler = FormHandler.objects.get(
            function = 'swim.form.test_files.swimformhandler.donothing'
        )
        renderingarrangement = FormFieldArrangement.objects.create(
            name = 'TestRendering Form'
        )
        formfield = FormField.objects.create(
            form = renderingarrangement,
            name = 'testField',
            label = 'testLable',
            help_text = 'test Help Text',
            order = 1,
            type = FormFieldType.objects.get(name='text'),
            required = True
        )
        self.form = Form.objects.create(
            key = 'green',
            name = 'test_rendering',
            action = self.test_path,
            success_url = '/success',
            handler = self.handler,
            form_fields = renderingarrangement,
            validator = self.formvalidator,
        )
        expected_message = 'Fo'
        response = self.client.post(self.test_path, {'testField' : 'foo'})
        self.assertEqual(response.status_code, 302)

        response = self.client.get(self.test_path)
        self.assertTrue(
            smart_bytes(expected_message) in response.content,
            "Expected error message: [%s] not found in response body: %s" % (
                expected_message,
                response.content)
        )

    #---------------------------------------------------------------------------
    def testResourceFormAssociation(self):
        """
        Test that association of forms with resources and their template access.
        """
        pass
