from django.conf import settings

from swim.core import signals
from swim.core.management import (
    create_groups
)
from swim.core.models import (
    ContentSchema,
    ResourceType,
    ResourceTypeMiddlewareMapping,
    ResourceTypeMiddleware,
    ResourceTypeResponseProcessor,
    ResourceTypeResponseProcessorMapping,
)
from swim.content.models import (
    SiteWideContent,
    CopySlot,
)
from swim.form.models import (
    FormHandler,
    FormFieldArrangement,
    FormField,
    FormFieldType,
    Form,
    FormValidator,
)
from swim.membership import models, MEMBERSHIP_SITE_WIDE_CONENT_KEY
from swim.membership.models import Member



#-------------------------------------------------------------------------------
MEMBERSHIP_GROUPS = (
    ('Membership Manager', "membership", "add_member",),
    ('Membership Manager', "membership", "change_member",),
    ('Membership Manager', "membership", "delete_member",),
)


#-------------------------------------------------------------------------------
DEFAULT_REGISTRATION_EMAIL_TEMPLATE = """
Dear {{member.display_name}},

Thank you for becoming a member of {{site_domain}}

Please click the following link to both confirm your registration and set your password:
{{ confirmation_url }}
"""

#-------------------------------------------------------------------------------
DEFAULT_FORGOTTEN_PASSWORD_EMAIL_TEMPLATE = """
Dear {{member.display_name}},

Please click the following link to set a new password for your account:
{{ confirmation_url }}
"""

#-------------------------------------------------------------------------------
EMAIL_TEMPLATES = (
    # (key, template)
    ('registration_email_template', DEFAULT_REGISTRATION_EMAIL_TEMPLATE,),
    ('forgotten_password_email_template', DEFAULT_FORGOTTEN_PASSWORD_EMAIL_TEMPLATE,),
)


#-------------------------------------------------------------------------------
SWIM_MIDDLEWARE_PATHS = (
    # (function_name, resource_type)
    ('swim.membership.swimmiddleware.registration_form_middleware', 'Account Registration'),
    ('swim.membership.swimmiddleware.confirmation_password_form_middleware', 'Account Confirmation'),
    ('swim.membership.swimmiddleware.change_password_form_middleware', 'Change Password'),
    ('swim.membership.swimmiddleware.forgotten_password_form_middleware', 'Forgotten Password'),
    ('swim.membership.swimmiddleware.login_form_middleware', 'Login'),
    ('swim.membership.swimmiddleware.logout_middleware', 'Logout'),
    ('swim.membership.swimmiddleware.member_middleware', 'default'),
    ('swim.membership.swimmiddleware.membership_origin_middleware', 'Login/Registration Success'),
)
#-------------------------------------------------------------------------------
SWIM_RESPONSE_PROCESSOR_PATHS = (
    # (function_name, resource_type)
    ('swim.membership.swimresponseprocessor.breadcrumbs_cookie_setter', 'default'),
    ('swim.membership.swimresponseprocessor.membership_origin_cookie_setter', 'Login'),
    ('swim.membership.swimresponseprocessor.membership_origin_cookie_setter', 'Account Registration'),
)

#-------------------------------------------------------------------------------
LOGIN_FORM_FIELDS = (
    # (name, label, help_text, type, required),
    ('email_address', 'Email Address', '', 'email', True),
    ('password', 'Password', '', 'password', False),
)

LOGIN_FORM_DEFINITION = (
# (handler_function, key, name, action, success_url, validator)
    'swim.membership.swimformhandler.member_login_handler',
    'member_login_form', 'Member Login Form',
    '/accounts/login', '/accounts/login/success',
    'swim.membership.validator.member_login_validator',
)
#-------------------------------------------------------------------------------
REGISTRATION_FORM_FIELDS = (
    # (name, label, help_text, type, required),
    ('display_name', 'Display Name',
        'This will be used to identify you to other users on our site.', 'text', True),
    ('email_address', 'Email Address',
        'Your email address will not be publicly displayed on our site.', 'email', True),
    ('given_name', 'First Name', 'Optional', 'text', False),
    ('family_name', 'Last Name', 'Optional', 'text', False),
    ('postal_code', 'Postal Code', 'Optional', 'text', False),
)

# (handler_function, key, name, action, success_url, validator)
REGISTRATION_FORM_DEFINITION = (
    'swim.membership.swimformhandler.registration_handler',
    'member_registration_form', 'Member Registration Form',
    '/accounts/registration', '/accounts/registration/success',
    'swim.membership.validator.registration_validator'
)

#-------------------------------------------------------------------------------
CONFIRMATION_PASSWORD_FORM_FIELDS = (
    # (name, label, help_text, type, required),
    ('new_password', 'Choose Password',
        '', 'password', True),
    ('new_password_again', 'Re-Type Password',
        '', 'password', True),
    ('code', 'Code',
        '', 'hidden', False),
)
# (handler_function, key, name, action, success_url, validator)
CONFIRMATION_FORM_DEFINITION = (
    'swim.membership.swimformhandler.confirmation_password_handler',
    'confirmation_password_form', 'Confirmation Password Form',
    '/accounts/confirmation', '/accounts/confirmation/success',
    'swim.membership.validator.confirmation_password_validator',
)

#-------------------------------------------------------------------------------
CHANGE_PASSWORD_FORM_FIELDS = (
    # (name, label, help_text, type, required),
    ('current_password', 'Current Password',
        '', 'password', True),
    ('new_password', 'Choose Password',
        '', 'password', True),
    ('new_password_again', 'Re-Type Password',
        '', 'password', True),
)
# (handler_function, key, name, action, success_url, validator)
CHANGE_PASSWORD_FORM_DEFINITION = (
    'swim.membership.swimformhandler.change_password_handler',
    'change_password_form', 'Change Password Form',
    '/accounts/change-password', '/accounts/change-password/success',
    'swim.membership.validator.change_password_validator',
)

#-------------------------------------------------------------------------------
FORGOTTEN_PASSWORD_FORM_FIELDS = (
    # (name, label, help_text, type, required),
    ('email_address', 'Email Address',
        '', 'email', True),
)
# (handler_function, key, name, action, success_url, validator)
FORGOTTEN_PASSWORD_FORM_DEFINITION = (
    'swim.membership.swimformhandler.forgotten_password_handler',
    'forgotten_password_form', 'Forgotten Password Form',
    '/accounts/forgotten-password', '/accounts/forgotten-password/success',
    'swim.membership.validator.forgotten_password_validator',
)


#-------------------------------------------------------------------------------
FORM_ARRANGEMENTS = (
    # (form_arrangement_name, field_definitions, form_definition)
    ("Member Registration Fields Arrangement",
        REGISTRATION_FORM_FIELDS, REGISTRATION_FORM_DEFINITION),
    ('Confirmation Password Fields Arrangement',
        CONFIRMATION_PASSWORD_FORM_FIELDS, CONFIRMATION_FORM_DEFINITION),
    ('Change Password Fields Arrangement',
        CHANGE_PASSWORD_FORM_FIELDS, CHANGE_PASSWORD_FORM_DEFINITION),
    ('Forgotten Password Fields Arrangement',
        FORGOTTEN_PASSWORD_FORM_FIELDS, FORGOTTEN_PASSWORD_FORM_DEFINITION),
    ('Login Fields Arrangement',
        LOGIN_FORM_FIELDS, LOGIN_FORM_DEFINITION),
)

#-------------------------------------------------------------------------------
MEMBERSHIP_ACCOUNTS = (
    #( display_name, email_address, password ),
,
)

#-------------------------------------------------------------------------------
def sync_membership_swim_data(**kwargs):
    """Creates all of the forms related to the membership application.
    """
    # Create the appropriate group
    create_groups(MEMBERSHIP_GROUPS)

    for form_arrangement_name, field_definitions, form_definition in FORM_ARRANGEMENTS:
        # Create the Registration Form Field Arrangement
        try:
            form_arrangement = FormFieldArrangement.objects.get(
                    name = form_arrangement_name
                )
        except FormFieldArrangement.DoesNotExist:
            form_arrangement = FormFieldArrangement.objects.create(
                name = form_arrangement_name
            )
            for order, (name, label, help_text, type, required) in enumerate(field_definitions):
                formfield = FormField.objects.create(
                    form = form_arrangement,
                    name = name,
                    label = label,
                    help_text = help_text,
                    order = order+1,
                    type = FormFieldType.objects.get(name = type),
                    required = required
                )
        handler_function, key, name, action, success_url, validator = form_definition
        # Get a reference to the registration form_handler
        form_handler = FormHandler.objects.get(
                function = handler_function
            )

        form_validator = None
        if validator:
            form_validator, created = FormValidator.objects.get_or_create(
                    title = validator,
                    function = validator,
                )


        # Create the default Form
        try:
            form = Form.objects.get(
                key=key,
            )
        except Form.DoesNotExist:
            form = Form.objects.create(
                key=key,
                name=name,
                action = action,
                success_url = success_url,
                handler = form_handler,
                form_fields = form_arrangement,
                validator = form_validator
            )


    #---------------------------------------------------------------------------
    # Register the appropriate middleware on all of the paths.
    for function_name, type_title in SWIM_MIDDLEWARE_PATHS:
        content_schema, create = ContentSchema.objects.get_or_create(title = type_title)
        resource_type, created = ResourceType.objects.get_or_create(
                title=type_title,
            )
        resource_type.content_schema = content_schema
        resource_type.save()

        # Get a reference to the registration handler
        function = ResourceTypeMiddleware.objects.get(
                function = function_name,
            )
        # Create the ResourceTypeMiddlewareMapping default for confirmation
        try:
            mapping = ResourceTypeMiddlewareMapping.objects.get(
                    resource_type=resource_type,
                    function=function,
                )
        except ResourceTypeMiddlewareMapping.DoesNotExist:
            mapping = ResourceTypeMiddlewareMapping.objects.create(
                    resource_type=resource_type,
                    function=function,
                )

    #---------------------------------------------------------------------------
    # Register the appropriate response processors on all of the paths.
    for function_name, type_title in SWIM_RESPONSE_PROCESSOR_PATHS:
        resource_type, created = ResourceType.objects.get_or_create(
                title = type_title
            )

        # Get a reference to the registration handler
        function = ResourceTypeResponseProcessor.objects.get(
                function = function_name,
            )
        # Create the ResourceTypeMiddlewareMapping default for confirmation
        try:
            mapping = ResourceTypeResponseProcessorMapping.objects.get(
                    resource_type=resource_type,
                    function=function
                )
        except ResourceTypeResponseProcessorMapping.DoesNotExist:
            mapping = ResourceTypeResponseProcessorMapping.objects.create(
                    resource_type=resource_type,
                    function=function,
                )


    #---------------------------------------------------------------------------
    # Create the default email template
    membership_site_wide_copy = SiteWideContent.objects.create(
            key=MEMBERSHIP_SITE_WIDE_CONENT_KEY
        )
    for key, template in EMAIL_TEMPLATES:
        email_template = CopySlot.objects.create(
            order = 0,
            key = key,
            content_object = membership_site_wide_copy,
            body = template
        )


    #---------------------------------------------------------------------------
    # Create a single default member
    for display_name, email_address, given_name, family_name, password in MEMBERSHIP_ACCOUNTS:
        member, created = Member.objects.get_or_create(
            display_name = display_name,
            email_address = email_address,
            given_name = given_name,
            family_name = family_name,
        )

        if created:
            member.user.password = password
            member.user.is_active = True
            member.user.save()

signals.initialswimdata.connect(sync_membership_swim_data)
