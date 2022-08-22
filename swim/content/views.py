import os
import string
from datetime import datetime

from PIL import Image

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseNotFound,
    HttpResponseServerError,
    Http404
)
from django.template import loader, TemplateDoesNotExist
from django.template.defaultfilters import slugify
from django.shortcuts import get_object_or_404, render
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist

from swim.core import string_to_key
from swim.core.content import DJANGO_MODEL_SWIM_CONTENT_TYPE_LOOKUPS
from swim.core.models import ResourceType
from swim.core.http import AcceptElement, header_elements
from swim.design.models import ResourceTypeTemplateMapping
from swim.core.views import CoreView
from swim.core.models import Resource
from swim.content.templatetags import swim_tags

from swim.content.models import (
    Page,
    SiteWideContent,
)

#-------------------------------------------------------------------------------
class HTTPError406(Exception):
    """
    An error that indicates we were not able to satisfy the requested media type.
    """

#-------------------------------------------------------------------------------
class ContentKeyMapper(dict):
    """
    This is a dictionary extention that will allow the template the ability to do lookups of the
    form content.type.key which is mapped to type.objects.get(key=key)
    """
    def __init__(self, contentclass, request):
        self._contentclass = contentclass
        self._request = request
        self._class_lookup = {}
        for content_object in DJANGO_MODEL_SWIM_CONTENT_TYPE_LOOKUPS.values():
            self._class_lookup[content_object.get_context_name()] = content_object.lookup_key

    def set_context(self, context):
        self._context = context

    def __getitem__(self, key):
        try:
            # Get the piece of content
            return self._class_lookup.get(self._contentclass, None)(key, self._request)
        except ObjectDoesNotExist as e:
            return ''

    def get(self, key, x):
        self[key] or x

#-------------------------------------------------------------------------------
class PageView(CoreView):
    #---------------------------------------------------------------------------
    def get_last_path_atom(self, path):
        path_atoms = path.strip("/").split("/")
        last = path_atoms.pop()
        path = "/%s" % ("/".join(path_atoms).lower(),)

        return path, last

    #---------------------------------------------------------------------------
    def __call__(self, request):
        """Method is called when SWIM routes the requests to this class.

        This method handles the CMS resource requests for SWIM.

        There are three hooks provided by this default view in it's processing.
        1) The process determines if a resource exists for the request resource.
           Hook1: match_resource
        2) A matching template which can render the resource into the requested
           content-type is found.
           Hook2: match_template
        3) The view requests that a context be generated.
           Hook3: get_context
        4) Any registered middleware are run and given access to the request,
           context, resource and template.
        5) The template is rendered with the returned context from steps 3 and 4
        6) Any registered response processors are run and given access to the
           request, context, resource template and response.
        7) Finally the response is returned.
        """
        self.request = request
        path = "/%s" % request.path.split('#')[0].strip('/')
        path = path.lower()

        # Match the incoming path to a Page object
        resource = self.match_resource(path, request)

        try:
            template = self.match_template(
                request,
                resource,
            )
        except HTTPError406 as e:
            # According to [1] HTTP/1.1 servers are allowed to return responses
            # that don't match the accept header.  We should consider choosing the first
            # template (according to our priority) and returning it when we can't find
            # an appropriate match.
            #
            # [1] -http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
            response = HttpResponse(str(e), status = 406)
            return response

        # used by the context processor as part of the Context
        request.resource = resource
        request.http_content_type = template.http_content_type

        # used by the SCOR's to avoid recursion problems
        request.recursion_guard_dict = {}
        context = self.get_context(request)
        context['resource'] = resource

        if getattr(settings, 'SWIM_RUN_MIDDLEWARE', True):
            self.run_middleware(resource.resource_type, request, context, resource, template)

        response = self.get_response(request, context, template)

        if getattr(settings, 'SWIM_RUN_RESPONSE_PROCESSOR', True):
            self.run_response_processors(
                    resource.resource_type, request, context, resource, template, response)

        return response

    #---------------------------------------------------------------------------
    def get_response(self, request, context, swim_template):
        # Render the template and create the response.
        return render(request, swim_template.path, context, content_type=str(swim_template.http_content_type))

    #---------------------------------------------------------------------------
    def run_middleware(self, resource_type, request, context, resource, template):
        for middleware in resource_type.get_middleware():
            middleware.function.invoke(request, context, resource, template)

    #---------------------------------------------------------------------------
    def run_response_processors(self, resource_type, request, context, resource, template, response):
        for response_processor in resource_type.get_response_processors():
            response_processor.function.invoke(request, context, resource, template, response)

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
            page = Page.objects.select_related(
                    "resource_type___swim_content_type"
                ).get(path = path)

        except Page.DoesNotExist as e:
            request.message_404 = 'No matching page found for path %s.' % path
            raise Http404(request.message_404)

        return page

    #---------------------------------------------------------------------------
    def match_template(self, request, resource):
        """Given a request path, will return a Template object or raise a Http404

        Arguments:
        request
            The incoming request from which desired content-type can be found.
        resource
            The resource which is to be rendered from which the appropriate
            template mapping can be found.
        """
        # Entry level into our content object system is always Resource
        swim_content_type = Resource.swim_content_type()

        # Find all of the Resource templates for this resource_type ,
        template_set = ResourceTypeTemplateMapping.get_potential_templates(
                request,
                resource.resource_type,
                swim_content_type,
            )

        # Gather the lists of the user agent's accepted media and the
        # types of media that we are able to produce from this resource.
        possible_templates = [rttm.template for rttm in template_set]

        return self.accept(request, possible_templates)

    #---------------------------------------------------------------------------
    def get_context(self, request):
        return {"request": request}


    #---------------------------------------------------------------------------
    def accept(self, request, possible_templates):
        """
        Yield the client's preferred media-types (from the given Content-Types).

        If 'possible_templates' is provided, it should be the prioritized list of
        templates which can be emitted for the current resource. The client's
        acceptable media 'accepted_media' (as given from the 'Accept' header in
        the given request) will be matched in order to these Content-Type
        values; the first template found will be returned.

        If no match is found, then HTTPError406 (Not Acceptable) is raised.

        Note that most web browsers send */* as a (low-quality) acceptable
        media range, which should match any Content-Type. In addition, "...if
        no Accept header field is present, then it is assumed that the client
        accepts all media types."

        Matching types are checked in order of client preference first,
        and then in the order of the given 'possible_templates' values.

        Note that this function does not honor accept-params (other than "q").
        """
        accepted_media = header_elements('Accept', request.META.get('HTTP_ACCEPT', '*/*') or '*/*')

        if possible_templates:
            # Note that 'accepted_media' is sorted in order of preference
            for element in accepted_media:
                if element.qvalue > 0:
                    if element.value == "*/*":
                        # Matches any type or subtype
                        return possible_templates[0]
                    elif element.value.endswith("/*"):
                        # Matches any subtype
                        mtype = element.value[:-1]  # Keep the slash
                        for template in possible_templates:
                            m = AcceptElement.from_str(template.http_content_type).value
                            if m.startswith(mtype):
                                return template
                    else:
                        # Matches exact value
                        for template in possible_templates:
                            m = AcceptElement.from_str(template.http_content_type).value
                            if element.value == m:
                                return template

        # No suitable media-range found.
        accept_header = request.META.get('HTTP_ACCEPT', '*/*')
        possible_media_types = []
        for template in possible_templates:
                possible_media_types.append(
                    AcceptElement.from_str(template.http_content_type).value)

        if len(possible_media_types) > 0:
            msg = "Your client sent this Accept header: %s."\
                " But no matching template was found that can produce these types."\
                " This resource only emits these media types: %s." %\
                    (accept_header,", ".join(possible_media_types))
        else:
            msg = "Your client sent this Accept header: %s."\
                " But no matching template was found that can produce these media types." %\
                    (accept_header,)
        raise HTTPError406(msg)



#-------------------------------------------------------------------------------
class Resource404:
    def __init__(self):
        self.resource_type = ResourceType.objects.get(key='not_found_404')

#-------------------------------------------------------------------------------
class ResourceView404(PageView):
    """View that services 404 requests

    The view will look to the design, then system templates for the 404 template.
    If the database doesn't contain a template of path /404_html, then it
    will look on disk for a 404.html template.
    """

    #---------------------------------------------------------------------------
    def match_resource(self, path, request):
        return Resource404()

    #---------------------------------------------------------------------------
    def get_context(self, request):
        context = super(ResourceView404, self).get_context(request)
        context.update({
            'message_404': getattr(
                request,
                'message_404',
                "We're sorry but the resource you are looking for does not exist."
            )
        })

        return context

    #---------------------------------------------------------------------------
    def get_response(self, request, context, template):
        return render(
                request,
                template.path,
                context,
                status=404,
                content_type=str(template.http_content_type)
            )

    #---------------------------------------------------------------------------
    def run_middleware(self, resource_type, request, context, resource, template):
        try:
            super(ResourceView404, self).run_middleware(
                    resource_type, request, context, resource, template)
        except Http404:
            # We're already in a 404 handler - ignore this new one.
            pass

    #---------------------------------------------------------------------------
    def run_response_processors(self, resource_type, request, context, resource, template, response):
        try:
            super(ResourceView404, self).run_response_processors(
                    resource_type, request, context, resource, template, response)
        except Http404:
            # We're already in a 404 handler - ignore this new one.
            pass

def view404(request, exception):
    """Wrapping method that invokes the ResourceView404 object for 404 requests.
    """
    return ResourceView404()(request)

#-------------------------------------------------------------------------------
class ResourceView500:
    """View that services 500 requests

    The view will look to the design, then system templates for the 500 template.
    If the database doesn't contain a template of path /500_html, then it
    will look on disk for a 500.html template.
    """

    def __call__(self, request):
        request.page = Resource()
        try:
            template = loader.get_template('/system/default/500')
        except TemplateDoesNotExist:
            template = loader.get_template('500.html')

        # Using a Context gives the 500 template access to all content
        context = {"request": request}
        return HttpResponseServerError(template.render(context))

def view500(request):
    """Wrapping method that invokes the ResourceView500 object for 500 requests.
    """
    return ResourceView500()(request)
