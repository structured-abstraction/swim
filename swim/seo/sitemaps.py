"""Provides a global hook for use with the sitemaps framework."""
from django.contrib.sitemaps import Sitemap

from swim.core import get_object_by_path
#from swim.seo.models import SitemapRule

#-------------------------------------------------------------------------------
class SwimSitemap(Sitemap):
    """
    Base class for all swim sitemaps which inherit from HasSEOAttributes
    """
    model = None

    def changefreq(self, obj):
        return obj.sitemap_change_frequency

    def priority(self, obj):
        return obj.sitemap_priority / 10.0

    def items(self):
        return self.model.objects.filter(sitemap_include=True)

    def lastmod(self, obj):
        return obj.modifieddate

    # This isn't needed as the get_absolute_url is good enough.
    # def location(self, obj):

sitemap_dict = {}
