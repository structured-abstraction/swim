"""
Response processors that are related to swim.membership
"""
import base64
import json
from swim.membership import (
        BREADCRUMBS_COOKIE_NAME,
        MEMBERSHIP_ORIGIN_COOKIE_NAME,
    )

#-------------------------------------------------------------------------------
def breadcrumbs_cookie_setter(request, context, resource, template, response):
    """
    Stores a cookie that includes the URL where they came from.
    """
    try:
        resource = context['resource']
        breadcrumbs = {
                "path": getattr(request, 'path', None),
                "title": getattr(resource, 'title', None)
            }
        response.set_cookie(
                key=BREADCRUMBS_COOKIE_NAME,
                value=base64.b64encode(json.dumps(breadcrumbs).encode('ascii')),
            )
    except KeyError:
        return

breadcrumbs_cookie_setter.title = "Track the last page they loaded."
breadcrumbs_cookie_setter.response_processor = True

#-------------------------------------------------------------------------------
def membership_origin_cookie_setter(request, context, resource, template, response):
    """
    Uses the breadcrumbs to store the last page they visited before registration/login.
    """
    breadcrumbs_string = request.COOKIES.get(BREADCRUMBS_COOKIE_NAME)
    if breadcrumbs_string:
        try:
            breadcrumbs_dict = json.loads(base64.b64decode(breadcrumbs_string))
            # Don't bother storing ourselves as the path.
            if breadcrumbs_dict['path'] != request.path:
                response.set_cookie(
                        key=MEMBERSHIP_ORIGIN_COOKIE_NAME,
                        value=base64.b64encode(json.dumps(breadcrumbs_dict).encode('ascii'))
                    )
        except ValueError:
            return

membership_origin_cookie_setter.title = "Track the page that started them on the registration process."
membership_origin_cookie_setter.response_processor = True
