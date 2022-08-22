from django.http import HttpResponse

from swim.core.views import CoreView
from swim.redirect.models import PathRedirect

#-------------------------------------------------------------------------------
class HttpResponseRedirect(HttpResponse):

    def __init__(self, status_code, redirect_to):
        self.status_code = status_code
        HttpResponse.__init__(self)
        self['Location'] = redirect_to

#-------------------------------------------------------------------------------
class RedirectView(CoreView):

    #---------------------------------------------------------------------------
    def __call__(self, request):
        path = request.path

        redirect = PathRedirect.objects.get(path=path)

        # Construct a full path (with QS args) with the new path.
        redirect_path = request.get_full_path().replace(path, redirect.redirect_path)

        return HttpResponseRedirect(redirect.redirect_type, redirect_path)
