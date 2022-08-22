import os
import traceback

from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils.encoding import smart_bytes

import swim
from swim.test import TestCase
from swim.core import is_subpath_on_path
from swim.core.paginator import DualPaginator
from swim.core.http import HeaderElement, AcceptElement
from swim.core.validators import isAlphaNumericURL

from swim.core.models import (
    ResourceType,
    RequestHandlerMapping,
    RequestHandler,
)

#-------------------------------------------------------------------------------
class GETHandler:
    def __call__(self, request):
        return HttpResponse("GETHandler")

#-------------------------------------------------------------------------------
class POSTHandler:
    def __call__(self, request):
        return HttpResponse("POSTHandler")

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class RequestHandlerTests(TestCase):
    """A bundle of tests to exercise the Request Handler algorithms.
    """

    def test_request_handler_algorithm(self):
        GETHandlerFunction = RequestHandler.objects.create(
            title = 'GET Handler',
            function = 'swim.core.tests.GETHandler',
        )
        POSTHandlerFunction = RequestHandler.objects.create(
            title = 'POST Handler',
            function = 'swim.core.tests.POSTHandler',
        )

        # Before any request handlers are installed
        # ALL urls must 404.
        response = self.client.get("/get")
        self.assertEqual(404, response.status_code)

        response = self.client.post("/post")
        self.assertEqual(404, response.status_code)

        get_handler = RequestHandlerMapping.objects.create(
            content_object = GETHandlerFunction,
            path='/get',
            method='GET',
            constructor = GETHandlerFunction,
        )
        post_handler = RequestHandlerMapping.objects.create(
            content_object = POSTHandlerFunction,
            path='/post',
            method='POST',
            constructor = POSTHandlerFunction,
        )

        # We have a GET handler installed for /get
        # Other URLs must STILL 404 for both method methods.
        # POST to /get and subtree should return 405
        # and the allow header should be set.
        test_cases = (
            # (url, method, status_code, expected_response, allow_header),
            ('/not-exist', 'GET', 404, None, None),
            ('/not-exist', 'POST', 404, None, None),
            ('/get', 'GET', 200, "GETHandler", None),
            ('/get', 'POST', 405, None, "GET"),
            ('/post', 'GET', 405, None, "POST"),
            ('/post', 'POST', 200, "POSTHandler", "GET"),
        )
        for url, method, status, expected, allow_header in test_cases:
            if method == "GET":
                response = self.client.get(url)
            elif method == "POST":
                response = self.client.post(url)

            self.assertEqual(status, response.status_code)
            if expected:
                self.assertEqual(
                        1, response.content.count(smart_bytes(expected)),
                        "Expected response [%s] not found in the actual response [%s]" % (
                            expected, response.content,
                        )
                    )

    def test_admin_without_slash_redirection(self):
        response = self.client.get("/admin")

        # Django now has a dedicated login page, so we are redirected there
        # on this request.
        self.assertRedirects(response, "/admin/", target_status_code=302)

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class SubpathOnPathTests(TestCase):
    """A bundle of tests to test out the if_subpath_on_path
    """

    def test_is_subpath_on_path(self):
        self.assertTrue(is_subpath_on_path('/art', '/art/foo'))
        self.assertTrue(is_subpath_on_path('/art/', '/art/foo'))
        self.assertTrue(is_subpath_on_path('/art/', '/art/foo/'))
        self.assertTrue(is_subpath_on_path('/art', '/art/foo/bar'))
        self.assertTrue(is_subpath_on_path('/art/', '/art/foo/bar'))
        self.assertTrue(is_subpath_on_path('/art/', '/art/foo/bar/'))

        self.assertFalse(is_subpath_on_path('/art', '/artisan'))
        self.assertFalse(is_subpath_on_path('/art/', '/artisan/'))
        self.assertFalse(is_subpath_on_path('/art', '/artisan/foo'))
        self.assertFalse(is_subpath_on_path('/art/', '/artisan/foo/'))
        self.assertFalse(is_subpath_on_path('/art', '/artisan/foo/bar'))
        self.assertFalse(is_subpath_on_path('/art/', '/artisan/foo/bar'))

#-------------------------------------------------------------------------------
class DualPaginatorTests(TestCase):
    """A bundle of tests to test out the DualPaginator
    """

    def test_dual_paginator(self):
        first_list = [1,2,3,4,5,6,7,8,9,10,11]
        second_list = [12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]

        paginator = DualPaginator(first_list, second_list, 10)

        # the full count must be equal to the len of both lists.
        self.assertEqual(paginator._get_count(), 26)

        # we must have cached the first and second counts as well.
        self.assertEqual(paginator._first_count, 11)
        self.assertEqual(paginator._second_count, 15)

        self.assertEqual(paginator.num_pages, 3)
        self.assertEqual(list(paginator.page_range), [1,2,3])

        page = paginator.page(1)
        self.assertEqual(page.object_list, [1,2,3,4,5,6,7,8,9,10])
        page = paginator.page(2)
        self.assertEqual(page.object_list, [11,12,13,14,15,16,17,18,19,20])
        page = paginator.page(3)
        self.assertEqual(page.object_list, [21,22,23,24,25,26])

    def test_heterogeneous_lists_dual_paginator(self):
        first_list = [1,2,3,4,]

        five = RequestHandler.objects.create(
                    title = '5',
                    function = 'swim.core.tests.GETHandler',
                )
        six = RequestHandler.objects.create(
                    title = '6',
                    function = 'swim.core.tests.POSTHandler',
                )
        second_list = [five, six]

        paginator = DualPaginator(first_list, second_list, 3)

        # the full count must be equal to the len of both lists.
        self.assertEqual(paginator._get_count(), 6)

        # we must have cached the first and second counts as well.
        self.assertEqual(paginator._first_count, 4)
        self.assertEqual(paginator._second_count, 2)

        self.assertEqual(paginator.num_pages, 2)
        self.assertEqual(list(paginator.page_range), [1,2])

        page = paginator.page(1)
        self.assertEqual(page.object_list, [1,2,3,])
        page = paginator.page(2)
        self.assertEqual(page.object_list, [4, five, six,])

#-------------------------------------------------------------------------------
class HeaderElementTests(TestCase):
    def test_index_error(self):
        try:
            fieldvalue = "text/html,;q=0.9,*/*;q=0.8"
            result = [AcceptElement.from_str(element) for element in fieldvalue.split(",") if element.strip()]
        except IndexError:
            self.fail("HeaderElement.parse incorrectly raise an index error")

#-------------------------------------------------------------------------------
class isAlphaNumericURLTests(TestCase):
    def test_isAlphaNumeriURL(self):
        valid_paths = [
            "/foo#something",
            "/foo.txt",
            "/foo-bar-baz.txt#id",
            "/~foo-bar-baz.txt#id",
        ]
        for path in valid_paths:
            try:
                isAlphaNumericURL(path)
            except ValidationError:
                self.fail("{0} is a valid path".format(path))
        invalid_paths = [
            "/foo&something",
            "/foo?txt=1&something",
        ]
        for path in invalid_paths:
            try:
                isAlphaNumericURL(path)
                self.fail("{0} is not a valid path".format(path))
            except ValidationError:
                pass



if __name__ == "__main__":
    run_tests()
