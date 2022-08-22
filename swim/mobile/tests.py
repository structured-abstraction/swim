from django.conf import settings

from django.test import override_settings
from swim.test import TestCase
from swim.mobile import (
    WANTS_DOMAIN_COOKIE_KEY,
    WANTS_GET_PARAM,
    WANTS_REGULAR_GET_VALUE,
    WANTS_MOBILE_GET_VALUE,
)


IPHONE_USER_AGENT = "Mozilla/5.0 (iPhone; U; XXXXX like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/241 Safari/419.3"

#-------------------------------------------------------------------------------
@override_settings(
    ALLOWED_HOSTS=['*'],
    MOBILE_DOMAIN='mobi.localhost',
    COOKIE_DOMAIN='.localhost',
    MIDDLEWARE=(
        'swim.thirdparty.minidetector.Middleware',
        'swim.mobile.MobileSiteRedirect',
    ) + settings.MIDDLEWARE,
    ROOT_URLCONF='swim.urls'
)
class MobileSiteRedirectTests(TestCase):
    """A bundle of tests to exercise the MobileSiteRedirectTests
    """

    def mobile_get(self, *args, **kwargs):
        kwargs['HTTP_USER_AGENT'] = IPHONE_USER_AGENT
        return self.client.get(
                *args,
                **kwargs
            )

    def test_basic_mobile_redirecting_workflow(self):
        # To start, we don't have the cookie.
        self.assertFalse(WANTS_DOMAIN_COOKIE_KEY in self.client.cookies)

        # on a none mobile device the response for a request for the none
        # mobile site will be a 200.
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        # and we'll still not have a cookie
        self.assertFalse(WANTS_DOMAIN_COOKIE_KEY in self.client.cookies)

        # on a mobile device all requests should redirect
        response = self.mobile_get("/")
        self.assertRedirects(response, "http://mobi.localhost/")
        # No cookie set.
        self.assertFalse(WANTS_DOMAIN_COOKIE_KEY in self.client.cookies)

        # subsequent request should still redirect
        response = self.mobile_get("/")
        self.assertRedirects(response, "http://mobi.localhost/")
        # No cookie set.
        self.assertFalse(WANTS_DOMAIN_COOKIE_KEY in self.client.cookies)

        # Mobile requests should succeed
        response = self.mobile_get("/", HTTP_HOST='mobi.localhost')
        self.assertEqual(response.status_code, 200)
        # STILL no cookie
        self.assertFalse(WANTS_DOMAIN_COOKIE_KEY in self.client.cookies)

        # HOWEVER, if we ask for the regular site WITH an appropriate get
        # parameter, it should allow us to see it. The first request will
        # redirect, but keep us on the regular site and will set the cookie.
        response = self.mobile_get("/", data={WANTS_GET_PARAM: WANTS_REGULAR_GET_VALUE})
        self.assertRedirects(response, "http://testserver/")
        # COOKIE SET
        self.assertTrue(WANTS_DOMAIN_COOKIE_KEY in self.client.cookies)
        self.assertEqual(self.client.cookies.get(WANTS_DOMAIN_COOKIE_KEY).value, WANTS_REGULAR_GET_VALUE)

        # Subsequent GETS to the normal site don't redirect
        response = self.mobile_get("/")
        self.assertEqual(response.status_code, 200)

        # Subsequent GETS to the mobile site don't redirect
        response = self.mobile_get("/", HTTP_HOST='mobi.localhost')
        self.assertEqual(response.status_code, 200)

        # Subsequent GETS to the normal site don't redirect
        response = self.mobile_get("/")
        self.assertEqual(response.status_code, 200)

        # HOWEVER, if we ask for the mobile site WITH an appropriate get
        # parameter, it should allow us to see it. The first request will
        # redirect, but keep us on the mobile site and will set the cookie.
        # and then they will always be redirected to the mobile again.
        response = self.mobile_get("/",
                data={WANTS_GET_PARAM: WANTS_MOBILE_GET_VALUE},
                HTTP_HOST='mobi.localhost'
            )
        self.assertRedirects(response, "http://mobi.localhost/")
        # COOKIE SET
        self.assertTrue(WANTS_DOMAIN_COOKIE_KEY in self.client.cookies)
        self.assertEqual(self.client.cookies.get(WANTS_DOMAIN_COOKIE_KEY).value, WANTS_MOBILE_GET_VALUE)

        # Subsequent requests for the regular site should redirect.
        response = self.mobile_get("/")
        self.assertRedirects(response, "http://mobi.localhost/")

        # Subsequent GETS to the mobile site don't redirect
        response = self.mobile_get("/", HTTP_HOST='mobi.localhost')
        self.assertEqual(response.status_code, 200)

        # Subsequent requests for the regular site should redirect.
        response = self.mobile_get("/")
        self.assertRedirects(response, "http://mobi.localhost/")

if __name__ == "__main__":
    run_tests()
