import datetime

from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseNotFound,
    HttpResponseServerError,
    Http404
)
from django.template import loader, TemplateDoesNotExist
from django.conf import settings

from swim.core import path_resolution_order, get_object_by_path
from swim.core.models import (
    Resource,
    ResourceType,
    RequestHandlerMapping,
)

# TODO: Remove this dependency on design
from swim.design.models import CSS, JavaScript

#-------------------------------------------------------------------------------
class CoreView:
    """Base class for view objects.
    """

    def __call__(self, request):
        raise NotImplementedError("Subclasses MUST implement __call__")


#-------------------------------------------------------------------------------
def default(request):
    """Routes incoming SWIM requests to the appropriate RequestHandlers.

    First, we look for a handler that matches the path and request method.
    If found, that handler is invoked and its response is returned. If no
    handlers are found that match the current path AND method type, then
    we look for handlers that match only on the current path. If none are
    found, then we return an Http404, if some are found, we return an HTTP
    405 with the appropriate Allow headers set.
    """
    request.types = {}
    request.resource_type_templates = {}

    path = "/%s" % request.path.strip('/')
    path = path.lower()

    try:
        request_handler = RequestHandlerMapping.objects.select_related("constructor").get(
                path=path,
                method=request.method,
            )
    except RequestHandlerMapping.DoesNotExist:
        request_handler = None

    # When a request handler is not found, we return one of a few errors.
    # if other request handlers exist for the given path, but have a different
    # method, then we return a 405.
    # if no request handlers exist for the given path we return a 404.
    if not request_handler:
        path_request_handlers = RequestHandlerMapping.objects.filter(
                path=path,
            )

        # There are NO potential handlers for this path.
        if path_request_handlers.count() == 0:
            request.message_404 = 'No matching request handler found for path %s.' % path
            raise Http404(request.message_404)

        potential_methods = set()
        for request_handler in path_request_handlers:
            potential_methods.add(request_handler.method)

        response = HttpResponse('Method not allowed.', status = 405)
        response['Allow'] = ' '.join(sorted(list(potential_methods)))
        return response

    # For methods that don't typically contain request bodies, we will redirect
    # to the canonical URL.
    if request.path != request_handler.path and request.method in ('GET', 'HEAD',):
        return HttpResponseRedirect(request_handler.path)

    request_handler_instance = request_handler.constructor.invoke()
    return request_handler_instance(request)

#-------------------------------------------------------------------------------
# css is served up slightly differently than normal content
def media(request, path=None, model=None, mimetype=None):
    media_path_list = path.split('/')
    media_object_list = model.objects.filter(path__in=media_path_list).order_by('-modifieddate')
    if not media_object_list:
        raise Http404('No media found at this url')

    # Start with a last modified date of 15 years ago.
    media_dict = dict([(media.path, media) for media in media_object_list])
    media_body_list = []
    latest_media = media_object_list[0]
    for media_path in media_path_list:
        try:
            media = media_dict[media_path]
        except KeyError:
            raise Http404('%s not found.' % media_path)
        media_body_list.append(media.body)

    response = HttpResponse('\n'.join(media_body_list), content_type=mimetype)
    response['Last-Modified'] = latest_media.http_last_modified()
    return response


#-------------------------------------------------------------------------------
def css(request, path=None):
    return media(request, path, CSS, 'text/css')

#-------------------------------------------------------------------------------
# css is served up slightly differently than normal content
def javascript(request, path=None):
    return media(request, path, JavaScript, 'text/javascript')

#-------------------------------------------------------------------------------
def admin_redirect(request):
    return HttpResponseRedirect("/admin/")

#-------------------------------------------------------------------------------
def firefox_35_tinymce_bug_view(request, image):
    return HttpResponseRedirect(settings.ADMIN_MEDIA_PREFIX + image)
