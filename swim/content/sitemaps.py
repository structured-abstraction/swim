from swim.content.models import Page
from swim.seo.sitemaps import SwimSitemap, sitemap_dict

#-------------------------------------------------------------------------------
class PageSitemap(SwimSitemap):
    model = Page
sitemap_dict['page'] = PageSitemap
