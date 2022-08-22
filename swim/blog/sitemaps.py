from swim.blog.models import Blog, Post
from swim.seo.sitemaps import SwimSitemap, sitemap_dict

#-------------------------------------------------------------------------------
class BlogSitemap(SwimSitemap):
    model = Blog
sitemap_dict['blogs'] = BlogSitemap

#-------------------------------------------------------------------------------
class PostSitemap(SwimSitemap):
    model = Post

    def items(self):
        return self.model.published_objects.filter(sitemap_include=True)

sitemap_dict['posts'] = PostSitemap
