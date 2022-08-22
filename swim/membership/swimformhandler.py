"""
SWIM Form handlers related to member registration.
"""
import base64
import json

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.sites.models import Site
from django.conf import settings
from django.template import Template, Context
from django.core import mail
from django.contrib import auth
from django.contrib.contenttypes.models import ContentType as DjangoContentType


from swim.membership.models import Member
from swim.content.models import (
    Page,
    SiteWideContent,
    CopySlot,
)
from swim.core.models import (
    ResourceTypeMiddlewareMapping,
    ResourceTypeMiddleware,
)
from swim.membership import (
    MEMBERSHIP_ORIGIN_COOKIE_NAME,
    MEMBERSHIP_SITE_WIDE_CONENT_KEY,
)

#-------------------------------------------------------------------------------
def registration_handler(request, form):
    """
    Handle the form submission for a member registration.

    Creates the member and sends the confirmation email.
    """

    # Create the member with the appropriate fields.
    member = Member.objects.create(
        display_name = form.cleaned_data['display_name'],
        given_name = form.cleaned_data['given_name'],
        family_name = form.cleaned_data['family_name'],
        email_address = form.cleaned_data['email_address'],
        postal_code = form.cleaned_data['postal_code'],
    )


    # Now we need to generate the email, which requires some references in
    # order to determine the URL appropriately.
    # Find the reference to the ResourceTypeMiddleware so we can determine
    # the URL on which the Confirmation ResourceTypeMiddlewareMapping will run.
    confirmation_function = ResourceTypeMiddleware.objects.get(
            function = 'swim.membership.swimmiddleware.confirmation_password_form_middleware'
        )
    # Stupid Django doesn't let me pass callable objects directly in
    # cause it'll try to call them - so pass an anonymous function.
    confirmation_code = ResourceTypeMiddlewareMapping.objects.get(
            function=confirmation_function
        )

    # TODO: This is strange?  Many different pages _could_ work here.
    page = Page.objects.filter(resource_type=confirmation_code.resource_type)[0]

    # Figure out our site name
    try:
        site_domain = Site.objects.get(id=settings.SITE_ID).domain
    except Site.DoesNotExist as e:
        site_domain = ""

    # Look up the template that we'll use to generate the message
    # and interpret it as a Django Template.
    membership_swc = SiteWideContent.objects.get(
            key = MEMBERSHIP_SITE_WIDE_CONENT_KEY
        )
    resource_type = DjangoContentType.objects.get_for_model(membership_swc)
    registration_confirmation_email_message = CopySlot.objects.get(
        order = 0,
        key = 'registration_email_template',
        django_content_type__id = resource_type.id,
        object_id = membership_swc.id,
    )
    t = Template(registration_confirmation_email_message._body)

    message = t.render(Context({
        'member': member,
        'site_domain': site_domain,
        'confirmation_url': "http://" + site_domain + page.path +
            '?code=' + member.change_password_code
    }))

    # And send the mail
    mail.send_mail(
        'Membership Confirmation - ' + site_domain,
        message,
        settings.SERVER_EMAIL,
        [member.email_address,]
    )

registration_handler.title = "Member Registration Handler"

#-------------------------------------------------------------------------------
def change_password_handler(request, form):
    if request.user.is_authenticated:
        request.user.set_password(form.cleaned_data['new_password'])
        request.user.save()
change_password_handler.title = "Change Member Password Handler"

#-------------------------------------------------------------------------------
def confirmation_password_handler(request, form):
    code = form.cleaned_data.get('code', None)
    if code:
        try:
            member = Member.objects.get(change_password_code=code)
        except Member.DoesNotExist:
            return HttpResponseRedirect(settings.LOGIN_URL)

        user = member.user
        user.set_password(form.cleaned_data['new_password'])
        user.is_active = True
        user.save()
        member.change_password_code = None
        member.save()
        user = auth.authenticate(username=user.username, password=form.cleaned_data['new_password'])
        if user and user.is_active:
            auth.login(request, user)
confirmation_password_handler.title = "Member Confirmation Handler"

#-------------------------------------------------------------------------------
def forgotten_password_handler(request, form):
    member = form.cleaned_data['member']
    member.create_change_password_code()

    # Now we need to generate the email, which requires some references in
    # order to determine the URL appropriately.
    # Find the reference to the ResourceTypeMiddleware so we can determine
    # the URL on which the Confirmation ResourceTypeMiddlewareMapping will run.
    change_password_function = ResourceTypeMiddleware.objects.get(
            function = 'swim.membership.swimmiddleware.confirmation_password_form_middleware'
        )
    # Stupid Django doesn't let me pass callable objects directly in
    # cause it'll try to call them - so pass an anonymous function.
    confirmation_code = ResourceTypeMiddlewareMapping.objects.get(
            function=change_password_function
        )

    # TODO: This is strange?  Many different pages _could_ work here.
    page = Page.objects.filter(resource_type=confirmation_code.resource_type)[0]

    # Figure out our site name
    try:
        site_domain = Site.objects.get(id=settings.SITE_ID).domain
    except Site.DoesNotExist as e:
        site_domain = ""

    # Look up the template that we'll use to generate the message
    # and interpret it as a Django Template.
    membership_swc = SiteWideContent.objects.get(
            key = MEMBERSHIP_SITE_WIDE_CONENT_KEY
        )
    resource_type = DjangoContentType.objects.get_for_model(membership_swc)
    forgotten_password_email_template = CopySlot.objects.get(
        order = 0,
        key = 'forgotten_password_email_template',
        django_content_type__id = resource_type.id,
        object_id = membership_swc.id,
    )
    t = Template(forgotten_password_email_template._body)

    message = t.render(Context({
        'member': member,
        'site_domain': site_domain,
        'confirmation_url': "http://" + site_domain + page.path +
            '?code=' + member.change_password_code
    }))

    # And send the mail
    mail.send_mail(
        'Forgotten Password Request - ' + site_domain,
        message,
        settings.SERVER_EMAIL,
        [member.email_address,]
    )
forgotten_password_handler.title = "Forgotten Password Handler"

#-------------------------------------------------------------------------------
def member_login_handler(request, form):
    member = form.cleaned_data['member']
    user = member.user
    user = auth.authenticate(username=user.username, password=form.cleaned_data['password'])
    if user and user.is_active:
        auth.login(request, user)
        origin_cookie = request.COOKIES.get(MEMBERSHIP_ORIGIN_COOKIE_NAME, '{}')
        try:
            origin_dict = json.loads(base64.b64decode(str(origin_cookie)))
            origin_path = origin_dict.get('path', None)
            if origin_path:
                return HttpResponseRedirect(origin_path)
        except (TypeError, ValueError):
            pass
member_login_handler.title = "Member Login Handler"
