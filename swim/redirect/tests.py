from django.contrib.sites.models import Site
from django.test import override_settings

from swim.content.tests.base import NoContentTestCase
from swim.redirect.models import PathRedirect

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class RedirectTest(NoContentTestCase):
    def test_redirect_types(self):

        # First let's ensure that there isn't a page that would normally work.
        response = self.client.get("/")
        self.assertEqual(response.status_code, 404)

        pr = PathRedirect.objects.create(
            path="/",
            redirect_type=301,
            redirect_path="/tags",
        )

        # This is a 301 redirect
        response = self.client.get("/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.get('Location'), '/tags')


        pr.redirect_type = 302
        pr.save()

        # This is a 302 redirect
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.get('Location'), '/tags')

        pr.redirect_type = 303
        pr.save()

        # This is a 303 redirect
        response = self.client.get("/")
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.get('Location'), '/tags')

        pr.redirect_type = 307
        pr.save()

        # This is a 307 redirect
        response = self.client.get("/")
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.get('Location'), '/tags')

    def test_query_string_preserved(self):

        # First let's ensure that there isn't a page that would normally work.
        response = self.client.get("/")
        self.assertEqual(response.status_code, 404)

        pr = PathRedirect.objects.create(
            path="/",
            redirect_type=301,
            redirect_path="/tags",
        )

        # This is a 301 redirect
        response = self.client.get("/?qs_param=2")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.get('Location'), '/tags?qs_param=2')

