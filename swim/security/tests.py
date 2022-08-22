from django.contrib.auth.models import User, Group, AnonymousUser
from django.test import override_settings

from swim.test import TestCase
from swim.security.models import SslEncryption, AccessRestriction

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class SslEncryptionTests(TestCase):
    def setUp(self):
        super(SslEncryptionTests, self).setUp()
        self.superuser = User.objects.create(
            username='superuser',
            email='superuser@example.com',
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        self.superuser.set_password('foo')
        self.superuser.save()

        self.staff = User.objects.create(
            username='staff',
            email='staff@staff.com',
            is_active=True,
            is_staff=True,
            is_superuser=False,
        )
        self.staff.set_password('foo')
        self.staff.save()

        self.normal_user = User.objects.create(
            username='normal',
            email='normal@example.com',
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        self.normal_user.set_password('foo')
        self.normal_user.save()

        self.normal_user_wo_group = User.objects.create(
            username='normal_user_wo_group',
            email='normal_user_wo_group@example.com',
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        self.normal_user_wo_group.set_password('foo')
        self.normal_user_wo_group.save()


        self.group = Group.objects.create(
            name='DaGroup',
        )
        self.normal_user.groups.add(self.group)
        self.normal_user.save()

        self.anonymous_user = AnonymousUser()

    def _testSecureRedirect(self, url):
        response = self.client.get(url)
        self.assertTrue(response.status_code in (301,302))
        self.assertTrue('https://' in response['Location'])
        self.assertTrue(url in response['Location'])

    def testForceSecureConnection(self):
        self.restriction = SslEncryption.objects.create(
            path='/secure',
            force_ssl_connection=True,
        )

        # Access to these urls _must_ redirect to a secure connection
        secure_urls = (
            '/secure',
            '/secure/subfolder',
            '/secure/sub/subfolder',
        )
        for url in secure_urls:
            self._testSecureRedirect(url)

        # Access to these urls _must_ not redirect to a secure connection
        non_secure_urls = (
            '/foo',
            '/foo/bar',
            '/foo/bar/baz',
            '/baz',
        )
        for url in non_secure_urls:
            response = self.client.get(url)
            self.assertFalse(response.status_code in (301, 302))


        # If we create a default rule that forces ssl access, then
        # ALL urls must redirect to secure connections.
        self.defaul_restriction = SslEncryption.objects.create(
            path='/',
            force_ssl_connection=True,
        )

        for url in secure_urls + non_secure_urls + ('/',):
            self._testSecureRedirect(url)

    def _testHasAccess(self, user, url, access_restriction):
        # In this very specific case, we define access to be:
        # a non 301 response. Because of the way the tests
        # are set up, it'll actually be a 404, but I don't
        # want to depend on that.
        if user != self.anonymous_user:
            if not self.client.login(username=user.username, password='foo'):
                self.fail("%s failed to login." % user.username)

        response = self.client.get(url)
        self.assertFalse(response.status_code in (301, 302))


        if user != self.anonymous_user:
            self.client.logout()

    def _testNoAccess(self, user, url, access_restriction):
        response = self.client.get(url)

        # In this very specific case we define the lack of access
        # based
        self.assertTrue(response.status_code in (301,302), "Got response: %d" % response.status_code)
        self.assertTrue(url in response['Location'])

    def testForceSecureConnection(self):
        self.restriction = SslEncryption.objects.create(
            path='/secure',
            force_ssl_connection=True,
        )

        # Access to these urls _must_ redirect to a secure connection
        secure_urls = (
            '/secure',
            '/secure/subfolder',
            '/secure/sub/subfolder',
        )
        for url in secure_urls:
            self._testSecureRedirect(url)

        # Access to these urls _must_ not redirect to a secure connection
        non_secure_urls = (
            '/foo',
            '/foo/bar',
            '/foo/bar/baz',
            '/baz',
        )
        for url in non_secure_urls:
            response = self.client.get(url)
            self.assertFalse(response.status_code in (301, 302))


        # If we create a default rule that forces ssl access, then
        # ALL urls must redirect to secure connections.
        self.defaul_restriction = SslEncryption.objects.create(
            path='/',
            force_ssl_connection=True,
        )
        for url in secure_urls + non_secure_urls + ('/',):
            self._testSecureRedirect(url)

    def _testHasAccess(self, user, url, access_restriction):
        # In this very specific case, we define access to be:
        # a non 301 response. Because of the way the tests
        # are set up, it'll actually be a 404, but I don't
        # want to depend on that.
        if user != self.anonymous_user:
            if not self.client.login(username=user.username, password='foo'):
                self.fail("%s failed to login." % user.username)

        response = self.client.get(url)
        self.assertFalse(response.status_code in (301, 302),
                "Got a redirect, when we didn't expect it: user: %s " \
                "response: %s" % (user, response)
            )


        if user != self.anonymous_user:
            self.client.logout()

    def _testNoAccess(self, user, url, access_restriction):
        response = self.client.get(url)

        # In this very specific case we define the lack of access
        # based
        self.assertTrue(response.status_code in (301, 302))
        self.assertTrue(access_restriction.redirect_path in response['Location'])

    def testAccessRestrictionsEveryone(self):
        self.restriction = AccessRestriction.objects.create(
            path='not-so-secure',
            only_allow='everyone',
        )
        # The everyone rule MUST allow everyone in.
        # including anonymous users.
        for user in (
            self.superuser,
            self.staff,
            self.normal_user,
            self.normal_user_wo_group,
            self.anonymous_user
        ):
            self._testHasAccess(user, '/not-so-secure', self.restriction)


    def testAccessRestrictionsSpecificGroups(self):
        self.restriction = AccessRestriction.objects.create(
            path='securificationify-the-nation',
            only_allow='specific_groups',
        )
        self.restriction.allow_groups.add(self.group)

        # Restricted to specific groups is more selective.
        # It MUST always allow the superuser
        # it MUST also allow users associated with one of the
        # groups associated with this rule.
        for user in (
            self.superuser,
            self.normal_user,
        ):
            self._testHasAccess(user, '/securificationify-the-nation', self.restriction)

        # Users NOT in the group, including staff MUST NOT be allowed to view
        # the content.
        # Additionally, The URL that is redirected to, MUST be the one from the
        # matching access_restrction.
        for user in (
            self.staff,
            self.normal_user_wo_group,
            self.anonymous_user
        ):
            self._testNoAccess(user, '/securificationify-the-nation', self.restriction)


    def testAccessRestrictionsAllUsers(self):
        self.restriction = AccessRestriction.objects.create(
            path='securificationify-the-nation',
            only_allow='all_users',
        )

        # the all_users restriction MUST allow all logged in users to access the content.
        for user in (
            self.superuser,
            self.normal_user,
            self.staff,
            self.normal_user_wo_group,
        ):
            self._testHasAccess(user, '/securificationify-the-nation', self.restriction)

        # the all_users restriction must disallow anonymous users access.
        # Additionally, The URL that is redirected to, MUST be the one from the
        # matching access_restrction.
        for user in (
            self.anonymous_user,
        ):
            self._testNoAccess(user, '/securificationify-the-nation', self.restriction)

    def testAccessRestrictionsAllStaff(self):
        self.restriction = AccessRestriction.objects.create(
            path='securificationify-the-nation',
            only_allow='all_staff',
        )

        # the all_staff restriction MUST allow only superusers and staff
        # to access the content.
        for user in (
            self.superuser,
            self.staff,
        ):
            self._testHasAccess(user, '/securificationify-the-nation', self.restriction)

        # the all_staff restriction must disallow all other users including anonymous users.
        # Additionally, The URL that is redirected to, MUST be the one from the
        # matching access_restrction.
        for user in (
            self.normal_user_wo_group,
            self.normal_user,
            self.anonymous_user,
        ):
            self._testNoAccess(user, '/securificationify-the-nation', self.restriction)

    def testAccessRestrictionsAllSuperusers(self):
        self.restriction = AccessRestriction.objects.create(
            path='securificationify-the-nation',
            only_allow='all_superusers',
        )

        # the all_superusers restriction MUST allow only superusers
        # to access the content.
        for user in (
            self.superuser,
        ):
            self._testHasAccess(user, '/securificationify-the-nation', self.restriction)

        # the all_superusers restriction must disallow all other users including
        # anonymous users and staff.
        # Additionally, The URL that is redirected to, MUST be the one from the
        # matching access_restrction.
        for user in (
            self.staff,
            self.normal_user_wo_group,
            self.normal_user,
            self.anonymous_user,
        ):
            self._testNoAccess(user, '/securificationify-the-nation', self.restriction)
