from django.db import models
from django.template.defaultfilters import slugify

from swim.core import modelfields
from swim.core.models import (
    RequestHandler,
    RequestHandlerMapping,
    Resource,
    ResourceType,
)
from swim.membership.models import Member
from swim.blog.models import Blog
from swim.core.content import register_content_object

#-------------------------------------------------------------------------------
class RSSFeed(Resource):
    path = modelfields.Path('path', unique=True)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)


    #--------------------------------------------------------------------------
    def url(self):
        if self.path.strip('/') == '':
            return '/'
        else:
            return '/%s' % self.path.strip('/')

    #--------------------------------------------------------------------------
    def get_request_handler(self):
        obj, _ = RequestHandler.objects.get_or_create(
                title = 'swim.syndication.views.RSSView',
                function = 'swim.syndication.views.RSSView',
            )
        return obj

    #---------------------------------------------------------------------------
    def get_request_method(self):
        return "GET"

#-------------------------------------------------------------------------------
register_content_object('rssfeed', RSSFeed)
