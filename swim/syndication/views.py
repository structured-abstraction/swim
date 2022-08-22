from swim.content.views import PageView
from swim.syndication.models import RSSFeed

#-------------------------------------------------------------------------------
class RSSView(PageView):

    #---------------------------------------------------------------------------
    def match_resource(self, path, request):
        """Given a request path, will return a Page object or raise a Http404

        Arguments:
        path - A string of the form: \"/path/subpath\"
        request - A HttpRequest object
        """

        # Pages in swim are matched against a lowercase system path so that
        # the path /Eagle and /eagle are equivalent.
        path = path.lower()

        try:
            page = RSSFeed.objects.get(path = path)

        except Page.DoesNotExist as e:
            request.message_404 = 'No matching rss feed found for path %s.' % path
            raise Http404(request.message_404)

        return page

    #---------------------------------------------------------------------------
    def get_context(self, request):
        context = super(RSSView, self).get_context(request)
        context['feed'] = request.resource
        context['blog'] = request.resource.blog
        return context


