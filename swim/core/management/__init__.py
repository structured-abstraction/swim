from inspect import getargspec
from django.db import IntegrityError, models as DjangoModels
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.contrib.auth.models import User, Permission, Group

from swim.core import signals
from swim.core import models
from swim.core.models import (
    ModelIsContentType,
    RequestHandler,
    ContentSchema,
    ContentSchemaMember,
    ArrangementType,
    Resource,
    ResourceType,
    ResourceTypeMiddleware,
    ResourceTypeResponseProcessor,
    ResourceTypeSwimContentTypeMapping,
)
from swim.design.models import Template

#-------------------------------------------------------------------------------
def register_swim_code(modules, model, argspec):
    """Loads callable items from the given modules into the database

    Arguments:
    modules - The modules to load callables from
    model - The model to save the callables into
    argspec - A tuple of arguments that the callables must accept
    """

    # Iterate over the modules and try to import everything
    # out of them. Then iterate over the callables in the modules
    # and add them to a database table
    for module in modules:
        try:
            # Try to import the module
            imported_module = __import__(module, globals(), locals(), ['*'])
            # Iterate over the items defined in the module
            for key, potential_swim_code in imported_module.__dict__.items():

                # Skip over the items defined in the module
                if key.startswith('__'):
                    continue

                # Skip over the non-callable definitions
                if not callable(potential_swim_code):
                    continue

                # Check the argument spec of any callable definition
                try:
                    spec = getargspec(potential_swim_code)
                    if spec[0] != argspec:
                        continue
                except TypeError as e:
                    continue

                # If the callable has a title, use it.
                title = getattr(potential_swim_code, 'title', '%s.%s' % (module, key,))
                try:
                    entry, created = model.objects.get_or_create(
                        function=module + '.' + key,
                        title=title,
                    )
                except IntegrityError as e:
                    pass # Skip duplicate inserts

        except Exception as e:
            raise

#-------------------------------------------------------------------------------
def register_swim_middleware(**kwargs):
    """Loads all the callable items in the list of modules given in SWIM_MIDDLEWARE_MODULES
    """
    register_swim_code(
        settings.SWIM_MIDDLEWARE_MODULES,
        ResourceTypeMiddleware,
        ['request', 'context', 'resource', 'template']
    )

signals.initialswimdata.connect(register_swim_middleware)

#-------------------------------------------------------------------------------
def register_swim_context_processor(**kwargs):
    """Loads all the callable items in the list of modules given in SWIM_CONTEXT_PROCESSOR_MODULES
    """
    register_swim_code(
        settings.SWIM_CONTEXT_PROCESSOR_MODULES,
        ResourceTypeResponseProcessor,
        ['request', 'context', 'resource', 'template', 'response']
    )

signals.initialswimdata.connect(register_swim_context_processor)

#-------------------------------------------------------------------------------
def register_default_type(**kwargs):
    """Registers the default Resource Types that we use.
    """
    default_content_schema, created = ContentSchema.objects.get_or_create(title='default')
    default_type, created = ResourceType.objects.get_or_create(key='default')
    default_type.content_schema = default_content_schema
    default_type.title = 'default'
    default_type.save()


    _404_content_schema, created = ContentSchema.objects.get_or_create(title='default')
    _404_type, _ = ResourceType.objects.get_or_create(
            parent=default_type,
            key='not_found_404',
            title='404 Not Found',
            content_schema=_404_content_schema,
        )

    _500_content_schema, created = ContentSchema.objects.get_or_create(title='default')
    _500_type, _ = ResourceType.objects.get_or_create(
            parent=default_type,
            key='internal_error_500',
            title='500 Internal Server Error',
            content_schema=_500_content_schema,
        )


signals.initialswimdata.connect(register_default_type)


CONTENT_EDITOR_PERMISSIONS = (
    # (app_label, codename)
)

DEFAULT_SWIM_GROUPS = (
        # ( name, permissions )
        ('Content Editor', CONTENT_EDITOR_PERMISSIONS),
    )

DEFAULT_SWIM_USERS = (
    # ( username, db_password_entry, first_name, last_name, email_address, staff, active, superuser)
    ,
)

#------------------------------------------------------------------------------
def create_groups(group_list):
    for group_name, app_label, codename in group_list:
        group, created = Group.objects.get_or_create(name=group_name)

        perm = Permission.objects.get(
                content_type__app_label=app_label,
                codename=codename
            )
        group.permissions.add(perm)
        group.save()

#-------------------------------------------------------------------------------
def register_swim_users(**kwargs):
    """Registers the default SWIM users that we use.
    """
    #---------------------------------------------------------------------------
    for username, pw, first, last, email, staff, active, superuser, group_names in DEFAULT_SWIM_USERS:
        user, created = User.objects.get_or_create(
            username=username,
            email=email,
        )

        if created:
            user.password = pw
            user.first_name = first
            user.last_name = last
            user.is_staff = staff
            user.is_active = active
            user.is_superuser = superuser
            user.save()
            for group_name in group_names:
                group, created = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)


signals.initialswimdata.connect(register_swim_users)


#-------------------------------------------------------------------------------
def create_resource_types(types):
    for parent, key, title, swim_content_type_callable, content_schema_members in types:
        content_schema, _ = ContentSchema.objects.get_or_create(title=title)
        if not parent:
            # Make the resource types that we'll use
            resource_type, created = ResourceType.objects.get_or_create(
                key=key,
                title=title,
            )
            resource_type.content_schema = content_schema
            resource_type.save()
        else:
            parent = ResourceType.objects.get(key=parent)
            resource_type, created = ResourceType.objects.get_or_create(
                key=key,
                title=title,
            )
            resource_type.parent=parent
            resource_type.content_schema = content_schema
            resource_type.save()

        if created:
            if swim_content_type_callable:
                ResourceTypeSwimContentTypeMapping.objects.create(
                        resource_type=resource_type,
                        swim_content_type=swim_content_type_callable()
                    )
            if content_schema_members:
                #---------------------------------------------------------------
                for order, key, title, cardinality, swim_content_type in content_schema_members:
                    ContentSchemaMember.objects.create(
                            content_schema=content_schema,
                            order=order,
                            key=key,
                            title=title,
                            cardinality=cardinality,
                            swim_content_type=swim_content_type()
                        )

#-------------------------------------------------------------------------------
def create_arrangement_types(types):
    for key, title, content_schema_members, template_path, template_body in types:
        content_schema, _ = ContentSchema.objects.get_or_create(title=title)
        resource_type, created = ArrangementType.objects.get_or_create(
            key=key,
            title=title,
            content_schema=content_schema,
        )
        if content_schema_members:
            #---------------------------------------------------------------
            for order, key, title, cardinality, swim_content_type in content_schema_members:
                ContentSchemaMember.objects.create(
                        content_schema=content_schema,
                        order=order,
                        key=key,
                        title=title,
                        cardinality=cardinality,
                        swim_content_type=swim_content_type()
                    )
