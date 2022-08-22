from django.conf import settings
from django.test import TestCase
from django.core import mail
from django.contrib import auth
from django.template import Context, Template as DjangoTemplate
from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.test import override_settings
from django.utils.encoding import  smart_bytes

from swim.core.models import (
    ContentSchema,
    Resource,
    ResourceType,
    ResourceTypeMiddleware,
    ResourceTypeMiddlewareMapping,
)
from swim.design.models import (
    ResourceTypeTemplateMapping,
)

from swim.content.models import (
    Page,
    SiteWideContent,
    CopySlot,
)
from swim.design.models import Template
from swim.form.models import (
    FormFieldArrangement,
    FormField,
    Form,
    FormHandler,
    FormFieldType,
    FormFieldConstructor,
    FormFieldValidator
)

from swim.membership.models import Member
from swim.membership.validator import registration_validator
from swim.membership import (
    BREADCRUMBS_COOKIE_NAME,
    MEMBERSHIP_ORIGIN_COOKIE_NAME,
    MEMBERSHIP_SITE_WIDE_CONENT_KEY,
)
from swim.test import TestCase

#-------------------------------------------------------------------------------
@override_settings(DEBUG=True, ROOT_URLCONF='swim.urls')
class MembershipTests(TestCase):
    """A suite of tests for exercising the swim.membership module
    """

    #---------------------------------------------------------------------------
    def setUp(self):
        from django.conf import settings
        super(MembershipTests, self).setUp()
        self.display_name = 'example.foo.2'
        self.display_name_with_spaces = 'ex ample .fo o.2'
        self.member_email = 'webmaster@example.com'
        self.action = '/accounts/registration'
        self.success_url = '/accounts/registration/success'

        # Create some test pages / content

        # Index Page
        self.index_path = '/index'
        self.template = Template.objects.create(
            path = self.index_path,
            http_content_type = 'text/html; charset=utf-8',
            body = '''
                {% load swim_tags %}{% render content.form.member_registration_form %}
                ''',
            swim_content_type = Resource.swim_content_type()
        )
        self.index_schema = ContentSchema.objects.create(title = 'index')
        self.index_type = ResourceType.objects.create(
            title = 'index',
            content_schema = self.index_schema,
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.index_type,
            template = self.template
        )
        self.page = Page.objects.create(
            path = self.index_path,
            resource_type = self.index_type,
            title = 'index page'
        )

        # Confirmation page.
        self.template = Template.objects.create(
            path = '/accounts/confirmation',
            http_content_type = 'text/html; charset=utf-8',
            body = '''
                {% load swim_tags %}{% render confirmation_password_form %}
            ''',
            swim_content_type = Resource.swim_content_type(),
        )
        self.confirmation_type = ResourceType.objects.get(
            title = 'Account Confirmation',
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.confirmation_type,
            template = self.template
        )
        self.page = Page.objects.create(
            path = '/accounts/confirmation',
            resource_type = self.confirmation_type,
            title = 'test page'
        )

        # Confirmation success page
        self.template = Template.objects.create(
            path = '/accounts/confirmationpage',
            http_content_type = 'text/html; charset=utf-8',
            body = '{{ origin_url }} {{ origin_title }}',
            swim_content_type = Resource.swim_content_type(),
        )
        self.confirmation_type = ResourceType.objects.get(
            title = 'Login/Registration Success',
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.confirmation_type,
            template = self.template
        )
        self.page = Page.objects.create(
            path = '/accounts/confirmation/success',
            resource_type = self.confirmation_type,
            title = 'test page success'
        )

        # Change password
        self.template = Template.objects.create(
            path = '/accounts/change-password',
            http_content_type = 'text/html; charset=utf-8',
            body = '''
                {% load swim_tags %}{% render change_password_form %}
            ''',
            swim_content_type = Resource.swim_content_type(),
        )
        self.change_password_type = ResourceType.objects.get(
            title = 'Change Password',
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.change_password_type,
            template = self.template
        )
        self.page = Page.objects.create(
            path = '/accounts/change-password',
            resource_type = self.change_password_type,
            title = 'test page'
        )

        # Forgotten password
        self.template = Template.objects.create(
            path = '/accounts/forgotten-password',
            http_content_type = 'text/html; charset=utf-8',
            body = '''
                {% load swim_tags %}{% render forgotten_password_form %}
            ''',
            swim_content_type = Resource.swim_content_type()
        )
        self.forgotten_password_type = ResourceType.objects.get(
            title = 'Forgotten Password',
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.forgotten_password_type,
            template = self.template
        )
        self.page = Page.objects.create(
            path = '/accounts/forgotten-password',
            resource_type = self.forgotten_password_type,
            title = 'test page'
        )

        # Login
        self.template = Template.objects.create(
            path = '/accounts/login',
            http_content_type = 'text/html; charset=utf-8',
            body = '''
                {% load swim_tags %}{% render member_login_form %}
            ''',
            swim_content_type = Resource.swim_content_type()
        )
        self.login_type = ResourceType.objects.get(
            title = 'Login',
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.login_type,
            template = self.template
        )
        self.page = Page.objects.create(
            path = '/accounts/login',
            resource_type = self.login_type,
            title = 'test page'
        )
        self.page = Page.objects.create(
            path = '/accounts/login/success',
            resource_type = self.login_type,
            title = 'test page'
        )

        # Logout
        self.template = Template.objects.create(
            path = '/accounts/logout',
            http_content_type = 'text/html; charset=utf-8',
            body = 'You\'ve been logged out. Please Come Again',
            swim_content_type = Resource.swim_content_type()
        )
        self.login_type = ResourceType.objects.get(
            title = 'Logout',
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.login_type,
            template = self.template
        )
        self.page = Page.objects.create(
            path = '/accounts/logout',
            resource_type = self.login_type,
            title = 'test page'
        )


    #---------------------------------------------------------------------------
    def test_management_runs_properly(self):
        """Test that all of the approrpriate pieces of data are in place.
        """

        #-----------------------------------------------------------------------
        # The appropriate form handlers MUST be installed properly.
        test_cases = (
            'swim.membership.swimformhandler.registration_handler',
            'swim.membership.swimformhandler.change_password_handler',
            'swim.membership.swimformhandler.confirmation_password_handler',
            'swim.membership.swimformhandler.forgotten_password_handler',
        )
        for function in test_cases:
            try:
                registration_handler = FormHandler.objects.get(function=function)
            except FormHandler.DoesNotExist:
                self.fail("swim.membership MUST define a %s handler." % function)


        #-----------------------------------------------------------------------
        # The appopriate form field arrangement must exist:
        test_cases = (
            ('Member Registration Fields Arrangement',
                'member_registration_form', '/accounts/registration', '/accounts/registration/success'),
            ('Confirmation Password Fields Arrangement',
                'confirmation_password_form', '/accounts/confirmation', '/accounts/confirmation/success'),
            ('Change Password Fields Arrangement',
                'change_password_form', '/accounts/change-password', '/accounts/change-password/success'),
            ('Forgotten Password Fields Arrangement',
                'forgotten_password_form', '/accounts/forgotten-password', '/accounts/forgotten-password/success'),
        )
        for arrangement_name, form_key, action, success_url in test_cases:
            try:
                arrangement = FormFieldArrangement.objects.get(
                        name = arrangement_name
                    )
            except FormFieldArrangement.DoesNotExist:
                self.fail("%s Must Exist" % (arrangement_name,))


            # The appopriate form must exist:
            try:
                registration_form = Form.objects.get(
                        key = form_key,
                    )
                self.assertEqual("%s" % registration_form.action, action)
                self.assertEqual("%s" % registration_form.success_url, success_url)
            except Form.DoesNotExist:
                self.fail("%s Must Exist" % (form_key,))

        #-----------------------------------------------------------------------
        # The appopriate confirmation middleware must exist:
        test_cases = (
            # (function_name, path)
            ('swim.membership.swimmiddleware.confirmation_password_form_middleware', 'Account Confirmation'),
            ('swim.membership.swimmiddleware.change_password_form_middleware', 'Change Password'),
            ('swim.membership.swimmiddleware.forgotten_password_form_middleware', 'Forgotten Password'),
        )
        for function_name, type_title in test_cases:
            try:
                pt = ResourceType.objects.get(
                        title = type_title,
                    )
                ptm = ResourceTypeMiddleware.objects.get(
                        function=function_name,
                    )
                ptmm = ResourceTypeMiddlewareMapping.objects.get(
                        resource_type = pt,
                        function=ptm
                    )

            except ResourceType.DoesNotExist:
                self.fail("ResourceType at %s Must Exist" % type_title)
            except ResourceTypeMiddleware.DoesNotExist:
                self.fail("ResourceTypeMiddleware at %s Must Exist" % type_title)
            except ResourceTypeMiddlewareMapping.DoesNotExist:
                self.fail("ResourceTypeMiddlewareMapping at %s Must Exist" % type_title)

        #-----------------------------------------------------------------------
        # The appopriate email_template must exist
        try:
            membership_swc = SiteWideContent.objects.get(
                    key = MEMBERSHIP_SITE_WIDE_CONENT_KEY
                )
            resource_type = DjangoContentType.objects.get_for_model(membership_swc)
        except SiteWideContent.DoesNotExist:
            self.fail("The Registration Site Wide Content Must Exist")

        try:
            forgotten_password_email_template = CopySlot.objects.get(
                order = 0,
                key = 'forgotten_password_email_template',
                django_content_type__id = resource_type.id,
                object_id = membership_swc.id,
            )
        except CopySlot.DoesNotExist:
            self.fail("The CopySlot for forgotten_password_email_template Must Exist")

        try:
            registration_confirmation_email_message = CopySlot.objects.get(
                order = 0,
                key = 'registration_email_template',
                django_content_type__id = resource_type.id,
                object_id = membership_swc.id,
            )
        except CopySlot.DoesNotExist:
            self.fail("The CopySlot for registration_email_template Must Exist")

    #---------------------------------------------------------------------------
    def test_empty_registration_fails(self):
        # Empty registration data MUST fail
        post_data = {
                'display_name': '',
                'email_address': '',
                'given_name': '',
                'family_name': '',
                'postal_code': '',
            }
        response = self.client.post(self.action, post_data)
        self.assertEqual(response.status_code, 302)

        # Check the error messages
        response = self.client.get(self.index_path)
        self.assertIn(b'This field is required', response.content)

    #---------------------------------------------------------------------------
    def test_bad_registration_data_fails(self):
        # Empty registration data MUST fail
        post_data = {
                'display_name': self.display_name,
                'email_address': 'aasdf@',
                'given_name': '',
                'family_name': '',
                'postal_code': '',
            }
        response = self.client.post(self.action, post_data)
        self.assertEqual(response.status_code, 302)

        # Check the error messages
        response = self.client.get(self.index_path)
        error_msg = 'Enter a valid email address.'
        self.assertContains(response, error_msg)

    #---------------------------------------------------------------------------
    def test_registration(self):
        """
        Ensure people can sign up, get an email, confirm and change their pws.
        """
        # Good Registration Data should succeed.
        post_data = {
                'display_name': self.display_name,
                'email_address': self.member_email,
                'given_name': '',
                'family_name': '',
                'postal_code': '',
            }
        response = self.client.post(self.action, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.success_url in response['Location'])
        try:
            member = Member.objects.get(email_address=self.member_email)
        except Member.DoesNotExist:
            self.fail("Member registration failed to create the member")

        self.assertTrue(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertTrue(
                member.email_address in  str(email.message()),
                'email_address: [%s] not found in email message: %s' % (
                    member.email_address, email.message()
                )
            )
        # The member MUST have user associated with it
        self.assertTrue(member.user is not None)

        # The user MUST _not_ be active.
        user = member.user
        self.assertFalse(user.is_active)

        # Posting the same registration data again MUST fail,
        # with an error message.
        post_data = {
                'display_name': self.display_name,
                'email_address': self.member_email,
                'given_name': '',
                'family_name': '',
                'postal_code': '',
            }
        response = self.client.post(self.action, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.success_url in response['Location'])

        # Check that the appropriate error messages are raised
        # when the email_address isn't unique
        post_data = {
                'display_name': self.display_name + '2',
                'email_address': self.member_email,
                'given_name': '',
                'family_name': '',
                'postal_code': '',
            }
        self.assertRaises(forms.ValidationError,
                registration_validator, None, post_data)

        # Check that the appropriate error messages are raised
        # when the display_name isn't unique.
        post_data = {
                'display_name': self.display_name,
                'email_address': 'a_' + self.member_email,
                'given_name': '',
                'family_name': '',
                'postal_code': '',
            }
        self.assertRaises(forms.ValidationError,
                registration_validator, None, post_data)

        # Check that the appropriate error messages are raised
        # when the display_name produces a non unique username
        # IE - when the display_name differs only in spaces
        #      from another display_name
        post_data = {
                'display_name': self.display_name_with_spaces,
                'email_address': 'a_' + self.member_email,
                'given_name': '',
                'family_name': '',
                'postal_code': '',
            }
        self.assertRaises(forms.ValidationError,
                registration_validator, None, post_data)

    #---------------------------------------------------------------------------
    def _signup(self, displayname, email):
        # Empty registration data MUST fail
        post_data = {
                'display_name': displayname,
                'email_address': email,
                'given_name': '',
                'family_name': '',
                'postal_code': '',
            }
        response = self.client.post(self.action, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.success_url in response['Location'])
        try:
            member = Member.objects.get(email_address=self.member_email)
        except Member.DoesNotExist:
            self.fail("Member registration failed to create the member")
        return member

    #---------------------------------------------------------------------------
    def _confirm_new_password(self, member, new_password):

        # in the tests we can hard code it cause we control the default
        confirmation_url = '/accounts/confirmation'


        pw_data = {
            'code': member.change_password_code,
            'new_password': new_password,
            'new_password_again': new_password,
        }
        response = self.client.post('/accounts/confirmation', pw_data)
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/accounts/confirmation', {'code': member.change_password_code})
        self.assertEqual(response.content.count(b"Passwords do not match"), 0)

        member = Member.objects.get(email_address=self.member_email)
        user = member.user
        self.assertTrue(user.is_active)
        self.assertTrue(member.change_password_code is None)
        return member

    #---------------------------------------------------------------------------
    def test_confirmation_links(self):
        # Loading any of the pages must track the location in the breadcrumbs
        response = self.client.get('/index')
        self.assertIn(BREADCRUMBS_COOKIE_NAME, response.cookies)

        # Loading the login page must ALSO set the previously visited page
        # as a membership origin
        response = self.client.get('/accounts/login')
        self.assertIn(BREADCRUMBS_COOKIE_NAME, response.cookies)
        self.assertIn(MEMBERSHIP_ORIGIN_COOKIE_NAME, response.cookies)

        member = self._signup(self.display_name, self.member_email)

        # in the tests we can hard code it cause we control the default
        confirmation_url = '/accounts/confirmation'

        # The arbitrary code simply inserts the confirmation code into the context
        # But in the case of a bogus code, it won't be there.
        response = self.client.get(confirmation_url, {'code': 'asdfasdfasdfadsf'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse('confirmation_password_form' in response.context)

        # In the case of a valid code the form should be there.
        response = self.client.get(confirmation_url, {'code': member.change_password_code})
        self.assertTrue('confirmation_password_form' in response.context[0])
        form = response.context[0]['confirmation_password_form']
        # The change_password_code MUST be in the form and the response.
        self.assertEqual(form._initial['code'], member.change_password_code)
        self.assertTrue(smart_bytes(member.change_password_code) in response.content)

        bad_pw_data = {
            'code': member.change_password_code,
            'new_password': '',
            'new_password_again': '',
        }
        response = self.client.post('/accounts/confirmation', bad_pw_data)
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/accounts/confirmation', {'code': member.change_password_code})
        self.assertEqual(response.content.count(b"This field is required"), 2)

        # Set the passwords to different things and ensure we get an error
        bad_pw_data['new_password'] = 'asdf'
        bad_pw_data['new_password_again'] = 'asdf-foo'
        response = self.client.post('/accounts/confirmation', bad_pw_data)
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/accounts/confirmation', {'code': member.change_password_code})
        self.assertEqual(response.content.count(b"Passwords do not match"), 1)

        # Set the passwords to the same thing and ensure no error.
        bad_pw_data['new_password'] = 'asdf'
        bad_pw_data['new_password_again'] = 'asdf'
        response = self.client.post('/accounts/confirmation', bad_pw_data)
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/accounts/confirmation', {'code': member.change_password_code})
        self.assertEqual(response.content.count(b"Passwords do not match"), 0)

        member = Member.objects.get(email_address=self.member_email)
        user = member.user
        self.assertTrue(user.is_active)
        self.assertTrue(member.change_password_code is None)


        # Set the passwords to the same thing and ensure no error.
        member = self._confirm_new_password(member, 'asdf')
        user = member.user
        self.assertTrue(user.is_active)
        self.assertTrue(member.change_password_code is None)

        self.assertTrue(user.check_password('asdf'))

        # Now that the process is finished, we should be redirected to the success page
        # and that page MUST contain the origin_url and origin_title in its context.
        response = self.client.get('/accounts/confirmation/success')
        self.assertEqual(200, response.status_code)
        context = response.context
        if isinstance(context, (list, tuple)):
            context = context[0]
        self.assertIn('origin_path', context)
        self.assertIn('origin_title', context)

        self.assertEqual(response.context['origin_path'], '/index')
        self.assertEqual(response.context['origin_title'], 'index page')

    #---------------------------------------------------------------------------
    def test_change_password_not_available_in_context_when_not_logged_in(self):
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')

        # Ensure that the change_password_form is on the page but no errors yet.
        response = self.client.get('/accounts/change-password')
        self.assertEqual(0, response.content.count(b"Invalid password"))
        self.assertEqual(0, response.content.count(b"Passwords do not match"))
        self.assertTrue('change_password_form' in response.context[0])

        self.client.logout()

        # Ensure that the change_password_form is on not on the page cause they
        # are not logged in.
        response = self.client.get('/accounts/change-password')
        self.assertFalse('change_password_form' in response.context)

    #---------------------------------------------------------------------------
    def test_change_password_bad_current_pw(self):
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')

        #-----------------------------------------------------------------------
        # Test that we can't change a password by submitting a bad old pw.
        bad_old_pw_data = {
            'current_password': 'asdf',
            'new_password': 'new-password',
            'new_password_again': 'new-password',
            }
        response = self.client.post('/accounts/change-password', bad_old_pw_data)
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/accounts/change-password')
        self.assertEqual(1, response.content.count(b"Invalid password"))
        self.assertEqual(0, response.content.count(b"Passwords do not match"))
        member = Member.objects.get(id=member.id)
        user = member.user
        self.assertFalse(user.check_password('new-password'))

    #---------------------------------------------------------------------------
    def test_change_password_bad_new_pw(self):
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')

        #-----------------------------------------------------------------------
        # Test that we can't change a password by submitting a bad new pw pair.
        bad_new_pw_data = {
            'current_password': 'password',
            'new_password': 'new-password',
            'new_password_again': 'new-password-asdf',
            }
        response = self.client.post('/accounts/change-password', bad_new_pw_data)
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/accounts/change-password')
        self.assertEqual(0, response.content.count(b"Invalid password"))
        self.assertEqual(1, response.content.count(b"Passwords do not match"))
        member = Member.objects.get(id=member.id)
        user = member.user
        self.assertFalse(user.check_password('new-password'))

    #---------------------------------------------------------------------------
    def test_change_password_good_new_pw(self):
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')

        #-----------------------------------------------------------------------
        # Test that valid data results in good password changes
        good_pw_data = {
            'current_password': 'password',
            'new_password': 'new-password',
            'new_password_again': 'new-password',
            }
        response = self.client.post('/accounts/change-password', good_pw_data)
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/accounts/change-password')
        self.assertEqual(0, response.content.count(b"Invalid password"))
        self.assertEqual(0, response.content.count(b"Passwords do not match"))

        member = Member.objects.get(id=member.id)
        user = member.user
        self.assertTrue(user.check_password('new-password'))

    #---------------------------------------------------------------------------
    def test_change_password_good_both_pw_not_logged_in(self):
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')
        self.client.logout()

        #-----------------------------------------------------------------------
        # Test that valid data results in good password changes
        good_pw_data = {
            'current_password': 'password',
            'new_password': 'new-password',
            'new_password_again': 'new-password',
            }
        response = self.client.post('/accounts/change-password', good_pw_data)
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/accounts/change-password')

        member = Member.objects.get(id=member.id)
        user = member.user
        self.assertFalse(user.check_password('new-password'))

    #---------------------------------------------------------------------------
    def test_forgotten_password_not_available_in_context_when_logged_in(self):
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')

        # Ensure that the forgotten_password_form is on the page but no errors yet.
        response = self.client.get('/accounts/forgotten-password')
        self.assertFalse('forgotten_password_form' in response.context)

        self.client.logout()

        # Ensure that the forgotten_password_form is on not on the page cause they
        # are not logged in.
        response = self.client.get('/accounts/forgotten-password')
        self.assertTrue('forgotten_password_form' in response.context[0])

    #---------------------------------------------------------------------------
    def test_forgotten_password_form_error_bad_email(self):
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')

        self.client.logout()

        # Ensure that the forgotten_password_form is on not on the page cause they
        # are not logged in.
        response = self.client.get('/accounts/forgotten-password')
        self.assertTrue('forgotten_password_form' in response.context[0])
        self.assertEqual(0, response.content.count(b'Invalid email address'))

        #-----------------------------------------------------------------------
        # Test that we can't reset a password by submitting a bad email address.
        bad_new_pw_data = {
            'email_address': 'bad@bad.com',
            }
        response = self.client.post('/accounts/forgotten-password', bad_new_pw_data)
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/accounts/forgotten-password')
        self.assertCount(1, b'Invalid email address', response.content)

        # Assert that the password wasn't _actually_ changed yet.
        member = Member.objects.get(id=member.id)
        user = member.user
        self.assertTrue(user.check_password('password'))

    #---------------------------------------------------------------------------
    def test_forgotten_password_form_error_good_email(self):
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')

        self.client.logout()
        mail.outbox = []

        # Ensure that the forgotten_password_form is on not on the page cause they
        # are not logged in.
        response = self.client.get('/accounts/forgotten-password')
        self.assertTrue('forgotten_password_form' in response.context[0])
        self.assertEqual(0, response.content.count(b'Invalid email address'))

        #-----------------------------------------------------------------------
        # Test that we can't reset a password by submitting a bad email address.
        bad_new_pw_data = {
            'email_address': self.member_email,
            }
        response = self.client.post('/accounts/forgotten-password', bad_new_pw_data)
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/accounts/forgotten-password')
        self.assertEqual(0, response.content.count(b'Invalid email address'))

        # Assert that the password wasn't _actually_ changed yet.
        member = Member.objects.get(id=member.id)
        user = member.user
        self.assertTrue(user.check_password('password'))

        # The member MUST have a new code, however
        self.assertNotEqual(None, member.change_password_code)

        # The member MUST have received a new email
        self.assertEqual(1, len(mail.outbox))
        email_message = str(mail.outbox[0].message())
        self.assertEqual(1, email_message.count(member.change_password_code))

        self._confirm_new_password(member, 'new-password')

        # Assert that the password is now changed properly
        member = Member.objects.get(id=member.id)
        user = member.user
        self.assertFalse(user.check_password('password'))
        self.assertTrue(user.check_password('new-password'))
        # The code must be invalidated as well
        self.assertEqual(None, member.change_password_code)

    #---------------------------------------------------------------------------
    def test_membership_filters(self):
        t = DjangoTemplate("{% load membership_filters %}{{foo|member}}")
        self.assertEqual("Non-member", t.render(Context({'foo': None})))

        # after logging in, the request.user is a member
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')
        self.assertEqual("example.foo.2", t.render(Context({'foo': member.user})))

        self.assertEqual("example.foo.2", t.render(Context({'foo': member})))

    #---------------------------------------------------------------------------
    def test_login_form_cookies(self):
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')

        # While the member is logged in, we shouldn't see the form!
        response = self.client.get('/accounts/login')
        self.assertEqual(200, response.status_code)
        self.assertFalse('member_login_form' in response.context)

        self.client.logout()

        self.client.cookies[MEMBERSHIP_ORIGIN_COOKIE_NAME] = object()

        # Valid Email + Valid Password should succeed
        valid_post_data = {'email_address': self.member_email, 'password': 'password'}
        response = self.client.post('/accounts/login', valid_post_data)
        self.assertTrue(response.cookies is not None)

    #---------------------------------------------------------------------------
    def test_login_form(self):
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')

        # While the member is logged in, we shouldn't see the form!
        response = self.client.get('/accounts/login')
        self.assertEqual(200, response.status_code)
        self.assertFalse('member_login_form' in response.context)

        self.client.logout()


        # Loading any of the pages must track the location in the breadcrumbs
        # We'll load this page first to ensure that they get redirected
        # properly on login.
        response = self.client.get('/index')
        self.assertIn(BREADCRUMBS_COOKIE_NAME, response.cookies)

        # When they are not logged in, the form should be there.
        response = self.client.get('/accounts/login')
        self.assertEqual(200, response.status_code)
        self.assertTrue('member_login_form' in response.context[0])


        # Bad email should fail regardless of correct password
        bad_login_data = [
            {'email_address': 'foo@foo.com', 'password': 'asdfasdf'},
            {'email_address': 'foo@foo.com', 'password': 'password'},
        ]
        for post_data in bad_login_data:
            response = self.client.post('/accounts/login', post_data, **{'HTTP_REFERER': '/accounts/login'})
            self.assertEqual(302, response.status_code)
            self.assertIn('/accounts/login', response['Location'])

            response = self.client.get('/accounts/login');
            self.assertIn(b'Invalid email address', response.content)


        # Valid Email + Bad Password should fail
        bad_login_data = [
            {'email_address': self.member_email, 'password': 'asdfasdf'},
            {'email_address': self.member_email, 'password': 'foo'},
            {'email_address': self.member_email, 'password': 'password2'},
        ]
        for post_data in bad_login_data:
            response = self.client.post('/accounts/login', post_data, **{'HTTP_REFERER': '/accounts/login'})
            self.assertEqual(302, response.status_code)
            self.assertIn('/accounts/login', response['Location'])

            response = self.client.get('/accounts/login');
            self.assertIn(b'Invalid password', response.content)

        # Valid Email + Valid Password should succeed
        valid_post_data = {'email_address': self.member_email, 'password': 'password'}
        response = self.client.post('/accounts/login', valid_post_data)
        self.assertTrue(response.cookies is not None)
        self.assertRedirects(response, '/index')

        # The member SHOULD be logged in now!
        response = self.client.get('/accounts/login')
        self.assertEqual(200, response.status_code)
        self.assertFalse('member_login_form' in response.context)

        self.client.logout()

        # The member SHOULD NOT be logged in now!
        response = self.client.get('/accounts/login')
        self.assertEqual(200, response.status_code)
        self.assertTrue('member_login_form' in response.context[0])

        member.user.is_active = False
        member.user.save()

        # Valid Email + Valid Password should not succeed if the user is inactive
        valid_post_data = {'email_address': self.member_email, 'password': 'password'}
        response = self.client.post('/accounts/login', valid_post_data, **{'HTTP_REFERER': '/accounts/login'})
        self.assertEqual(302, response.status_code)
        self.assertIn('/accounts/login', response['Location'])
        response = self.client.get('/accounts/login');
        self.assertIn(b'This account has been disabled', response.content)

    #---------------------------------------------------------------------------
    def test_logout(self):
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')

        # While the member is logged in, we shouldn't see the login form!
        response = self.client.get('/accounts/login')
        self.assertEqual(200, response.status_code)
        self.assertFalse('member_login_form' in response.context)

        response = self.client.get('/accounts/logout')
        self.assertEqual(200, response.status_code)
        self.assertTrue('You\'ve been logged out. Please come again')

        # The member should be logged out now, so they SHOULD see
        # a login form.
        response = self.client.get('/accounts/login')
        self.assertEqual(200, response.status_code)
        self.assertTrue('member_login_form' in response.context[0])


    #---------------------------------------------------------------------------
    def test_member_not_in_context_when_no_auth_user(self):
        # Before the user is logged in, there shouldn't be a "member" in the context
        response = self.client.get('/index')
        self.assertNotIn('member', response.context)


    #---------------------------------------------------------------------------
    def test_member_in_context_when_auth_user_is_member(self):
        # Sign 'em up. Log 'em in.
        member = self._signup(self.display_name, self.member_email)
        member = self._confirm_new_password(member, 'password')

        # After the user is logged in, there should be a "member" in the context
        response = self.client.get('/index')
        self.assertIn('member', response.context[0])


    #---------------------------------------------------------------------------
    def test_member_not_in_context_when_auth_user_is_not_member(self):
        # Log our admin in cuz they are not a member.
        user = User.objects.get(username='sa')
        user.set_password('12345') #lets give'em a new pw (just to be paranoid)
        user.save()
        self.client.login(username='sa', password="12345")

        # After the user is logged in, there shouldn't be a "member" in the context
        response = self.client.get('/index')
        self.assertNotIn('member', response.context)

