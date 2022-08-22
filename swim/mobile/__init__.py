"""
SWIM Facilities for dealing with mobile sites.
"""

from django.http import HttpResponseRedirect
from django.conf import settings

#-------------------------------------------------------------------------------
WANTS_DOMAIN_COOKIE_KEY = 'swim.mobile.domain-wants'

WANTS_GET_PARAM = 'wants-domain'
WANTS_MOBILE_GET_VALUE = 'mobile'
WANTS_REGULAR_GET_VALUE = 'regular'
POSSIBLE_WANTS = (
        WANTS_MOBILE_GET_VALUE,
        WANTS_REGULAR_GET_VALUE,
    )

#-------------------------------------------------------------------------------
class MobileSiteRedirect:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        """

        scheme = "http"
        if request.is_secure():
            scheme = "https"

        # If the parameter is in the the GET params, use it and remove it
        if request.GET.get(WANTS_GET_PARAM, None) in POSSIBLE_WANTS:
            wants = request.GET[WANTS_GET_PARAM]

            # Remove the parameter
            #del request.GET[WANTS_GET_PARAM]

            # redirect to the current domain path SANS GET Param
            url = '%s://%s%s' % (scheme, request.get_host(), request.get_full_path())
            url = url.replace("%s=%s" % (WANTS_GET_PARAM, wants,), '')
            if url.endswith('?'):
                url =url.replace("?", "")
            response = HttpResponseRedirect(url)
            cookie_domain = getattr(settings, 'COOKIE_DOMAIN', None)
            response.set_cookie(WANTS_DOMAIN_COOKIE_KEY, wants, domain=cookie_domain)
            return response

        # For non-mobile-devices do nothing!
        if not getattr(request, 'mobile', False):
            return self.get_response(request)

        mobile_domain = getattr(settings, 'MOBILE_DOMAIN', None)

        # if we don't have a mobile domain, don't do anything.
        if mobile_domain is None:
            return self.get_response(request)

        # At this point we know they are on a mobile phone.
        current_domain = request.get_host()

        # Check to see if we've redirected them to the mobile site already
        # in this session.  If we have, don't do it again.
        # we have have, do it right now.

        # default is WANTS MOBILE!
        wants = request.COOKIES.get(WANTS_DOMAIN_COOKIE_KEY, WANTS_MOBILE_GET_VALUE)

        # If we they want MOBILE and are NOT on mobile, redirect them
        if wants == WANTS_MOBILE_GET_VALUE and current_domain != mobile_domain:
            mobile_scheme = "http"
            should_be_secure = getattr(settings, 'MOBILE_WANTS_SECURE', False)
            if request.is_secure() and should_be_secure:
                mobile_scheme = "https"

            return HttpResponseRedirect('%s://%s%s' % (mobile_scheme, mobile_domain, request.get_full_path()))

        # otherwise - they're asking for what they want, ton'd redirect them.
        return self.get_response(request)

