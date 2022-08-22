from django.http import (
    HttpResponse,
    HttpResponseRedirect,
)

from swim.core.views import CoreView
from swim.form.models import Form

#-------------------------------------------------------------------------------
class FormView(CoreView):
    #--------------------------------------------------------------------------- 
    def __call__(self, request):
        self.request = request
        path = "/%s" % request.path.strip('/')
        path = path.lower()

        swim_form = self.match_form(path, request)

        # Validate the incoming data
        form = swim_form.django_form(request, request.POST)
        if form.is_valid():

            # run the functon and return anything that is retured by it
            response = swim_form.handler.invoke(request, form)
            if response is not None:
                return response

            # Then redirect to the success URL
            return HttpResponseRedirect(swim_form.success_url)

        else:
            # In the session, store the wrong data and redirect back to the referrer path
            # TODO: Avoid namespace collisions for separate forms based on the action of the form
            request.session['POST'] = {swim_form.key: request.POST}
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    #--------------------------------------------------------------------------- 
    def match_form(self, path, request):
        """Given a request path, will return a Form object

        Arguments:
        path - A string of the form: \"/path/subpath\"
        request - A HttpRequest object
        """

        # Note that action is different than all other paths in that it stores
        # a trailing slash.
        try:
            form = Form.objects.get(action = path)
        except Form.DoesNotExist as e:
            form = None
        return form
