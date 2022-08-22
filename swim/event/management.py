from swim.core import signals

from swim.core.management import create_groups, create_resource_types
from swim.event import models
from swim.event.models import Calendar, Event
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.core.models import (
    Resource,
    ResourceType,
    ResourceTypeMiddleware,
    ResourceTypeMiddlewareMapping,
)
from swim.content.models import (
    CopySlot,
    Page,
    Menu,
    Link,
    MenuLink,
)



#-------------------------------------------------------------------------------
SWIM_MIDDLEWARE_PATHS = (
    # (function_name, resource_type)
    ('swim.event.swimmiddleware.all_calendar_events', 'default'),
)

#-------------------------------------------------------------------------------
CALENDAR_GROUPS = (
    # (group_name, app_label, codename)
    ("Calendar Editor", "event", "add_calendar",),
    ("Calendar Editor", "event", "change_calendar",),
    ("Calendar Editor", "event", "delete_calendar",),
    ("Calendar Editor", "event", "add_event",),
    ("Calendar Editor", "event", "change_event",),
    ("Calendar Editor", "event", "delete_event",),
)

#-------------------------------------------------------------------------------
CALENDAR_TYPE_RESOURCE_INTERFACE = (
        # (order, key, header, cardinality, swim_content_type)
        (1, 'body', 'Description', 'single', CopySlot.swim_content_type,),
    )

#-------------------------------------------------------------------------------
EVENT_TYPE_RESOURCE_INTERFACE = (
        # (order, key, header, cardinality, swim_content_type)
        (1, 'description', 'Description', 'single', CopySlot.swim_content_type,),
    )

#-------------------------------------------------------------------------------
RESOURCE_TYPES = (
    # ( parent, key, title, swim_content_type, interface )
    ('default', 'calendar', 'Calendar', Calendar.swim_content_type,
        CALENDAR_TYPE_RESOURCE_INTERFACE),
    ('default', 'event', 'Event', Event.swim_content_type,
        EVENT_TYPE_RESOURCE_INTERFACE),
)


#-------------------------------------------------------------------------------
def sync_calendar_data(**kwargs):
    # Create the base group.
    create_groups(CALENDAR_GROUPS)

    #---------------------------------------------------------------------------
    # Create The Resource Types
    create_resource_types(RESOURCE_TYPES)

    #---------------------------------------------------------------------------
    # Create The Middleware that will run on each resource type
    for function_name, type_key in SWIM_MIDDLEWARE_PATHS:
        resource_type = ResourceType.objects.get(
                key=type_key
            )

        # Get a reference to the registration handler
        middleware = ResourceTypeMiddleware.objects.get(
                function = function_name,
            )
        # Create the ResourceTypeMiddlewareMapping default for confirmation
        try:
            resource_type_middleware_mapping = ResourceTypeMiddlewareMapping.objects.get(
                    resource_type=resource_type,
                    function=middleware
                )
        except ResourceTypeMiddlewareMapping.DoesNotExist:
            resource_type_middleware_mapping = ResourceTypeMiddlewareMapping.objects.create(
                    resource_type=resource_type,
                    function=middleware,
                )

    #---------------------------------------------------------------------------
    # The following definitions MUST not be run at the module level otherwise
    # they'll cause an IntegrityError because the database won't have been
    # created yet.
    HTTP_CONTENT_TYPE = 'text/html; charset=utf-8'
    BLOG_PAGE_TYPE = ResourceType.objects.get(key='blog')
    RESOURCE_SCO = Resource.swim_content_type()
    DEFAULT_RESOURCE_TYPE = ResourceType.objects.get(title='default')

    #---------------------------------------------------------------------------
    EVENT_TEMPLATES = [
    ]

    for path, http_content_type, swim_content_type, body, resource_type in EVENT_TEMPLATES:
        template, created = Template.objects.get_or_create(
            path = path,
            http_content_type = http_content_type,
            swim_content_type = swim_content_type
        )

        if created:
            template.body = body
            template.save()

        ResourceTypeTemplateMapping.objects.get_or_create(
            resource_type=resource_type,
            template=template
        )

signals.initialswimdata.connect(sync_calendar_data)
