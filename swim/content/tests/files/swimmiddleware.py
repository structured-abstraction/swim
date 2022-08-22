from django.http import HttpResponse, HttpResponseRedirect, Http404

#-------------------------------------------------------------------------------
def add_to_context(request, context, resource, template):
    context['key']  = 'What the hell.'

#-------------------------------------------------------------------------------
def return_404(request, context, resource, template):
    raise Http404

#-------------------------------------------------------------------------------
def cause_500(request, context, resource, template):
    return FakeClassThatIsntImported
