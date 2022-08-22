from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.functional import LazyObject, SimpleLazyObject

from swim.core.content import DJANGO_MODEL_SWIM_CONTENT_TYPE_LOOKUPS
from swim.content.views import ContentKeyMapper
from swim.content.models import (
    SiteWideContent,
)


#-------------------------------------------------------------------------------
class LazyLoadSite(LazyObject):

    #---------------------------------------------------------------------------
    def _setup(self):
        self._wrapped = Site.objects.get_current()
        # Add in the site wide content.
        for swc in SiteWideContent.objects.all():
            setattr(self._wrapped, swc.key, swc)

        return self._wrapped

#-------------------------------------------------------------------------------
def processor(request):
    """
    Populates the default SWIM context.

    Adds in the request, settings, site and site wide content into template
    context.
    """
    content_dict = {}
    for content_object in DJANGO_MODEL_SWIM_CONTENT_TYPE_LOOKUPS.values():
        content_dict[content_object.get_context_name()] = ContentKeyMapper(
                content_object.get_context_name(),
                request
            )

    # There are cases where django (and other apps) will override keys
    # at the top level of the context. A good example of this is django's
    # login view which overrides the site attribute - which masks our site
    # wide content. To avoid this - we are also making these same context
    # variables available as part of a top level "swim" namespace.  So you
    # can access these high level variables as: swim.site ...
    context = {
            'content': content_dict,
            'request' : request,
            'settings': settings,
            'site': LazyLoadSite(),
        }

    context['swim'] = context
    return context
