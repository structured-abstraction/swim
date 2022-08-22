"""These are in utils so that they are not run directly.
"""
#from xml.dom.ext.reader import Sax2
import xml.dom.minidom
from io import StringIO

from swim.test import TestCase
from django.test import override_settings
from django.utils import timezone
from django.conf import settings


#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class HasSEOAttributesTest(TestCase):

    #---------------------------------------------------------------------------
    def test_sitemap_exists(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)

        # sitemap MUST have the appropriate content-type
        self.assertTrue(response.has_header('Content-type'), "sitemap has no Content-type")
        self.assertTrue(response['Content-type']=='application/xml', "sitemap Content-type is %s" % response['Content-type'])

    #---------------------------------------------------------------------------
    def create_resource(self, path):
        raise NotImplementedError(
                """These tests must be subclassed and the """
                """create_resource method must be implemented"""
            )

    #---------------------------------------------------------------------------
    def test_models_included_in_sitemap(self):
        other_resource = self.create_resource("/other")
        other_resource.sitemap_change_frequency = "monthly"
        other_resource.sitemap_priority = 10
        other_resource.save()

        about_resource = self.create_resource("/about")
        about_resource.sitemap_change_frequency = "monthly"
        about_resource.sitemap_priority = 10
        about_resource.save()

        hidden_resource = self.create_resource("/hidden")
        hidden_resource.sitemap_include = False
        hidden_resource.sitemap_change_frequency = "monthly"
        hidden_resource.sitemap_priority = 10
        hidden_resource.save()

        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)

        doc = xml.dom.minidom.parseString(response.content)


        # Ensure that all of the paths that are marked to be included
        # are included.
        url_nodes = doc.getElementsByTagName('url')
        for resource in (
            other_resource, about_resource
        ):
            found = False
            for url in url_nodes:
                # This makes some assumptions about the well-formedness of the sitemap
                loc = url.getElementsByTagName('loc')[0].firstChild.nodeValue
                sitemap_change_frequency = url.getElementsByTagName('changefreq')[0].firstChild.nodeValue
                priority = url.getElementsByTagName('priority')[0].firstChild.nodeValue
                lastmod = url.getElementsByTagName('lastmod')[0].firstChild.nodeValue

                if loc.endswith(resource.url()):
                    found = True
                    # Now we test each of the above assumptions.
                    self.assertEqual(sitemap_change_frequency, resource.sitemap_change_frequency,
                        "Error in sitemap for url: %s changfreq: %s != %s" % (resource.url(), sitemap_change_frequency, resource.sitemap_change_frequency))
                    self.assertAlmostEquals(float(priority), float(resource.sitemap_priority) / 10.0, 1,
                        "Error in sitemap for url: %s priority: %s != %s" % (resource.url(), priority, resource.sitemap_priority / 10.0))

                    if settings.USE_TZ:
                        content_date = timezone.localtime(resource.modifieddate).strftime("%Y-%m-%d")
                    else:
                        content_date = resource.modifieddate.strftime("%Y-%m-%d")

                    self.assertEqual(lastmod, content_date,
                        "Error in sitemap for url: %s lastmod: %s != %s" % (resource.url(), lastmod, content_date))
            self.assertTrue(found, "%s was incorrectly excluded from the sitemap" % (resource.url(),))

        # Ensure that none of the paths which are explicitly not included
        # do not show up.
        for resource in (
            hidden_resource,
        ):
            for url in url_nodes:
                # This makes some assumptions about the well-formedness of the sitemap
                loc = url.getElementsByTagName('loc')[0].firstChild.nodeValue
                if loc.endswith(resource.url()):
                    self.fail("%s should not be included in the sitemap" % (resource.url(),))


    #---------------------------------------------------------------------------
    def test_meta_methods(self):
        other_resource = self.create_resource("/other")


        # When the meta rule turns off no_follow/no_index the
        # meta rule is empty.
        other_resource.meta_no_follow = False
        other_resource.meta_no_index = False
        other_resource.save()
        self.assertEqual("", other_resource.meta_robot())


        # however, if either one of them are true - we'll
        # get the appropriate output.
        other_resource.meta_no_follow = True
        other_resource.meta_no_index = False
        other_resource.save()
        self.assertEqual('<meta name="robots" content="index, nofollow">', other_resource.meta_robot())

        other_resource.meta_no_follow = False
        other_resource.meta_no_index = True
        other_resource.save()
        self.assertEqual('<meta name="robots" content="noindex, follow">', other_resource.meta_robot())

        other_resource.meta_no_follow = True
        other_resource.meta_no_index = True
        other_resource.save()
        self.assertEqual('<meta name="robots" content="noindex, nofollow">', other_resource.meta_robot())


if __name__ == "__main__":
    run_tests()
