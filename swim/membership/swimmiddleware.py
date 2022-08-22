"""
Membership related middleware
"""
import urllib.parse
import base64
import json

from django.contrib import auth
from swim.membership.models import Member
from swim.form.models import Form
from swim.membership import MEMBERSHIP_ORIGIN_COOKIE_NAME

#-------------------------------------------------------------------------------
def registration_form_middleware(request, context, resource, template):
    """
    Ensure the member exists and insert the appropriate form into the context.
    """
    member_registration_form = Form.objects.get(
            key='member_registration_form'
        )
    member_registration_form.set_request(request)
    context['member_registration_form'] = member_registration_form


#-------------------------------------------------------------------------------
def confirmation_password_form_middleware(request, context, resource, template):
    """
    Ensure the member exists and insert the appropriate form into the context.
    """
    code = request.GET.get('code', None)
    if code:

        # Member has clicked the link in their e-mail.
        try:
            member = Member.objects.get(change_password_code = code)
        except Member.DoesNotExist:
            return None

        confirmation_password_form = Form.objects.get(
                key='confirmation_password_form'
            )
        confirmation_password_form.initial_data({'code': code})
        confirmation_password_form.set_request(request)
        context['confirmation_password_form'] = confirmation_password_form

#-------------------------------------------------------------------------------
def change_password_form_middleware(request, context, resource, template):
    """
    Ensure the member exists and insert the appropriate form into the context.
    """
    if request.user.is_authenticated:
        change_password_form = Form.objects.get(
                key='change_password_form'
            )
        change_password_form.set_request(request)
        context['change_password_form'] = change_password_form

#-------------------------------------------------------------------------------
def forgotten_password_form_middleware(request, context, resource, template):
    """
    Ensure the member exists and insert the appropriate form into the context.
    """
    if not request.user.is_authenticated:
        forgotten_password_form = Form.objects.get(
                key='forgotten_password_form'
            )
        forgotten_password_form.set_request(request)
        context['forgotten_password_form'] = forgotten_password_form

#-------------------------------------------------------------------------------
def login_form_middleware(request, context, resource, template):
    """
    Ensure that the member is not logged in and then give them the form
    """
    if not request.user.is_authenticated:
        member_login_form = Form.objects.get(
            key='member_login_form'
        )
        member_login_form.set_request(request)
        context['member_login_form'] = member_login_form

#-------------------------------------------------------------------------------
def logout_middleware(request, context, resource, template):
    """
    Ensure that the member is logged out.
    """
    if request.user.is_authenticated:
        auth.logout(request)

#-------------------------------------------------------------------------------
def member_middleware(request, context, resource, template):
    """
    Ensure that the member is logged out.
    """
    if request.user.is_authenticated:
        try:
            member = Member.objects.get(user=request.user)
            for_her_pleasure = member
            context['member'] = for_her_pleasure

        except Member.DoesNotExist as e:
            pass


#-------------------------------------------------------------------------------
def membership_origin_middleware(request, context, resource, template):
    """
    Populates the context with up to two variables: origin_path and origin_page.

    If the MEMBERSHIP_ORIGIN_COOKIE_NAME cookie is set, this view will put it into the
    context at the key: origin_path.

    If origin_path is a page on our site, it will also populate the context with
    an instance to that page at the key: origin_page
    """
    breadcrumb = request.COOKIES.get(MEMBERSHIP_ORIGIN_COOKIE_NAME, None)
    if breadcrumb:
        try:
            breadcrumb_dict = json.loads(base64.b64decode(breadcrumb))

            context['origin_path'] = breadcrumb_dict.get('path', None)
            context['origin_title'] = breadcrumb_dict.get('title', None)
        except ValueError:
            return



