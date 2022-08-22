"""
Middleware processors for the security model.

Copyright (C) 2008 Structured Abstraction Inc.
"""

import base64

from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponsePermanentRedirect,
)
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

from swim.core import get_object_by_path, query_object_by_potential_paths
from swim.security.models import SslEncryption, AccessRestriction


#-------------------------------------------------------------------------------
def allow_superusers(middleware, access_restriction, request, path):
    if request.user.is_active and request.user.is_authenticated and \
            request.user.is_superuser:
        return middleware.get_response(request)

    # TODO: where do we redirect to?
    return HttpResponseRedirect("/login/")

#-------------------------------------------------------------------------------
def allow_staff(middleware, access_restriction, request, path):
    if request.user.is_active and request.user.is_authenticated and \
            request.user.is_staff:
        return middleware.get_response(request)
    # TODO: where do we redirect to?
    return HttpResponseRedirect("/login/")

#-------------------------------------------------------------------------------
def allow_users(middleware, access_restriction, request, path):
    if request.user.is_active and request.user.is_authenticated:
        return middleware.get_response(request)
    # TODO: where do we redirect to?
    return HttpResponseRedirect("/login/")

#-------------------------------------------------------------------------------
def allow_confirmed_email(middleware, access_restriction, request, path):
    # TODO: this is waiting on a way to determine if we have confirmed an email.
    return middleware.get_response(request)

#-------------------------------------------------------------------------------
def allow_specific_groups(middleware, access_restriction, request, path):
    if request.user.is_active and request.user.is_authenticated:

        # Get the users group queryset.
        user_group_qs = request.user.groups.all()

        # Get the access restriction groups query set
        access_restriction_groups = access_restriction.allow_groups.all()

        # filter the users groups by the groups in the access_restrction_groups
        user_group_qs.in_bulk([group.id for group in access_restriction_groups])

        # if there is at least one group in common, let them in.
        # Or if they are the superuser
        if len(user_group_qs) > 0 or request.user.is_superuser:
            return middleware.get_response(request)

    return HttpResponseRedirect(access_restriction.redirect_path)

#-------------------------------------------------------------------------------
def allow_everyone(middleware, access_restriction, request, path):
    return middleware.get_response(request)


#-------------------------------------------------------------------------------
only_allow_case = {
    'all_superusers': allow_superusers,
    'all_staff': allow_staff,
    'all_users': allow_users,
    'confirmed_email': allow_confirmed_email,
    'specific_groups': allow_specific_groups,
    'everyone': allow_everyone,
}

#-------------------------------------------------------------------------------
class EnforceAccessRestriction:
    """
    A middleware class to enforce access restrictions.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        access_restriction = query_object_by_potential_paths(AccessRestriction, path)
        if not access_restriction:
            # We don't care about this URL
            return self.get_response(request)

        # TODO: maybe put all of these on the AccessRestriction model itself?
        only_allow_key = access_restriction.only_allow
        return only_allow_case[only_allow_key](self, access_restriction, request, path)


#-------------------------------------------------------------------------------
def basic_challenge():
    response =  HttpResponse('Authorization Required', content_type="text/plain")
    response['WWW-Authenticate'] = 'Basic'
    response.status_code = 401
    return response

#-------------------------------------------------------------------------------
def basic_authenticate(authentication):
    (authmeth, auth) = authentication.split(' ',1)
    if 'basic' != authmeth.lower():
        return None

    auth = base64.b64decode(auth.strip()).decode('utf-8')
    username, password = auth.split(':', 1)
    AUTHENTICATION_USERNAME = getattr(settings, 'BASIC_WWW_AUTHENTICATION_USERNAME')
    AUTHENTICATION_PASSWORD = getattr(settings, 'BASIC_WWW_AUTHENTICATION_PASSWORD')
    return username == AUTHENTICATION_USERNAME and password == AUTHENTICATION_PASSWORD

#-------------------------------------------------------------------------------
class BasicAuthenticationMiddleware:

    #---------------------------------------------------------------------------
    def __init__(self, get_response):
        self.get_response = get_response

    #---------------------------------------------------------------------------
    def __call__(self, request):
        if getattr(settings, 'BASIC_WWW_AUTHENTICATION', False):
            roots = getattr(settings, 'BASIC_WWW_AUTHENTICATION_ROOTS', ['/'])
            excludes = getattr(settings, 'BASIC_WWW_AUTHENTICATION_EXCLUDES', [])

            if (any([request.path.startswith(root) for root in roots])
                and request.path not in excludes
            ):
                if 'HTTP_AUTHORIZATION' not in request.META:
                    return basic_challenge()

                authenticated = basic_authenticate(request.META['HTTP_AUTHORIZATION'])
                if not authenticated:
                    return basic_challenge()

        return self.get_response(request)

