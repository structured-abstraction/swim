from datetime import datetime, timedelta, date, time

from django.test import override_settings

from swim.test import TestCase
from swim.event.models import (
    Calendar,
    Event,
)
from swim.core.models import (
    ResourceType,
    ContentSchema,
    ContentSchemaMember,
)
from swim.content.models import CopySlot
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.chronology import utils as chronologytests
from swim.seo import utils as seo_test_utils

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class FunctionalCalendarFrontendTest(TestCase):
    """These tests make sure that after initial data installation the site is usable.
    """
    # TODO: implement some of these tests.

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class CalendarTests(chronologytests.TimelineTests):

    #---------------------------------------------------------------------------
    def setUp(self):
        super(CalendarTests, self).setUp()
        self.all_timeline_name = "all_calendar_events"
        self.timeline_resource_type = self.calendar_resource_type = ResourceType.objects.get(
                key='calendar',
            )
        self.event_content_schema = ContentSchema.objects.create(title="TNG Event")
        self.event_resource_type = ResourceType.objects.create(
                key = 'tng_event_other',
                title = 'TNG Event What?',
                content_schema = self.event_content_schema,
            )
        rti = ContentSchemaMember.objects.create(
                content_schema = self.event_content_schema,
                order = 0,
                key = "description",
                title = "Description",
                cardinality = 'single',
                swim_content_type = CopySlot.swim_content_type(),
            )
        rti = ContentSchemaMember.objects.create(
                content_schema = self.calendar_resource_type.content_schema,
                order = 0,
                key = "description",
                title = "Description",
                cardinality = 'single',
                swim_content_type = CopySlot.swim_content_type(),
            )


        self.show_resource_type = ResourceType.objects.create(
                key = 'show other',
                title = 'Show',
            )
        self.calendar_path = '/plus-15'
        self.timeline = self.calendar = Calendar.objects.create(
                path=self.calendar_path,
                title = 'Plus 15 Space',
            )
        self.calendar_path2 = '/main-space'
        self.timeline2 = self.calendar2 = Calendar.objects.create(
                path=self.calendar_path2,
                title = 'Main 15 Space',
            )

        self.timeline_event_set = self.timeline.event_set.all()
        self.start_datetime_attr = 'start_timestamp'
        self.end_datetime_attr = 'end_timestamp'
        self.resource_type_attr = 'resource_type'

    #---------------------------------------------------------------------------
    def _create_events(self, event_list, calendar=None):
        if calendar is None:
            calendar = self.calendar
        event_instance_list = []
        for event_type, title, start, end in event_list:
            resource_type = ResourceType.objects.get(key = event_type)
            if end:
                end_date = end.date()
                end_time = end.time()
            else:
                end_date = None
                end_time = None
            if start:
                start_date = start.date()
                start_time = start.time()
            else:
                start_date = None
                start_time = None
            event_instance_list.append(
                Event.objects.create(
                    resource_type=resource_type,
                    calendar=calendar,
                    title=title,
                    start_date = start_date,
                    end_date = end_date,
                    start_time = start_time,
                    end_time = end_time,
                )
            )
        return event_instance_list


    #---------------------------------------------------------------------------
    def test_calendar_view(self):
        response = self.client.get(self.calendar.url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['resource'], self.calendar)

    #---------------------------------------------------------------------------
    def test_calendar_template_context(self):
        description = "This is a description Fool!"
        rc = CopySlot.objects.create(
                order = 0,
                key = 'description',
                content_object = self.calendar,
                _body = description,
            )
        # Create a template that shows the description
        template = Template.objects.create(
                path="/calendar/current_month_view",
                body="""
                    {% load swim_tags %}{% render resource.copy.description %}
                """
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order=0,
            resource_type=self.calendar_resource_type,
            template=template
        )

        # the description must be in the result.
        response = self.client.get(self.calendar.url())
        self.assertEqual(response.status_code, 200)
        self.assertIn(description, response.content)

        # Try the same thing for an event.
        resource_type = ResourceType.objects.get(key = "tng_event_other")
        event = Event.objects.create(
                    resource_type=resource_type,
                    calendar=self.calendar,
                    title="event 1",
                    start_date = (datetime.now() - timedelta(days=1)).date(),
                    end_date = (datetime.now() + timedelta(days=1)).date(),
                    start_time = (datetime.now() - timedelta(days=1)).time(),
                    end_time = (datetime.now() + timedelta(days=1)).time(),
            )
        rc = CopySlot.objects.create(
                order = 0,
                key = 'description',
                content_object = event,
                _body = description,
            )

        # Create a template that shows the description
        template = Template.objects.create(
                path="/calendar/event/test",
                body="""
                    {% load swim_tags %}{% render resource.copy.description %}
                """
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order = 0,
            resource_type = self.event_resource_type,
            template = template
        )
        # the description must be in the result.
        response = self.client.get(event.url())
        self.assertEqual(response.status_code, 200)
        self.assertIn(description, response.content)

    #---------------------------------------------------------------------------
    def test_calendar_template_context_with_ranges(self):
        description = "This is a description Fool!"
        # Try showing the description of an event
        resource_type = ResourceType.objects.get(key = "tng_event")
        event = Event.objects.create(
                    resource_type=resource_type,
                    calendar=self.calendar,
                    title="event 1",
                    start_date = (datetime.now() - timedelta(days=1)).date(),
                    end_date = (datetime.now() + timedelta(days=1)).date(),
                    start_time = (datetime.now() - timedelta(days=1)).time(),
                    end_time = (datetime.now() + timedelta(days=1)).time(),
            )
        rc = CopySlot.objects.create(
                order = 0,
                key = 'description',
                content_object = event,
                _body = description,
            )

        rc = CopySlot.objects.create(
                order = 0,
                key = 'description',
                content_object = self.calendar,
                _body = description,
            )
        # Create a template that shows the description
        template = Template.objects.create(
                path="/calendar/current_month_view",
                body="""
                """
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order = 0,
            resource_type = self.calendar_resource_type,
            template = template
        )
        test_cases = (
            """
            {% load swim_tags %}{% get_resource for resource.all.all_types.events.0 as event %}
            {{event.title}}{% render event.copy.description %}""",
        )
        for template_body in test_cases:
            template.body=template_body
            template.save()

            # the description must be in the result.
            response = self.client.get(self.calendar.url())
            self.assertEqual(response.status_code, 200)
            self.assertIn(description, response.content)



#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class EventTests(TestCase):
    #---------------------------------------------------------------------------
    def test_event_view(self):
        self.event_resource_type = ResourceType.objects.get(
                key='event',
            )
        # Create a template that shows the description
        template = Template.objects.create(
                path="/calendar/event",
                body="""
                    {% load swim_tags %}{% render resource.copy.description %}
                """
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order=0,
            resource_type=self.event_resource_type,
            template=template
        )

        calendar_path = '/plus-15'
        calendar = Calendar.objects.create(
                path=calendar_path,
                title = 'Plus 15 Space',
            )

        event = Event.objects.create(
                calendar = calendar,
                title = 'Melanie Authier Presents',
                start_date = datetime.now(),
                end_date = datetime.now() + timedelta(weeks=1),
            )
        response = self.client.get(event.url())
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['resource'], event)

#-------------------------------------------------------------------------------
class CalendarSEOTests(seo_test_utils.HasSEOAttributesTest):
    #---------------------------------------------------------------------------
    def setUp(self):
        super(CalendarSEOTests, self).setUp()
        self.resource_type = ResourceType.objects.create(
            key='new_type',
            title = 'New Page Type',
        )

    #---------------------------------------------------------------------------
    def create_resource(self, path):
        return Calendar.objects.create(
                resource_type=self.resource_type,
                path=path,
                title=path,
            )

#-------------------------------------------------------------------------------
class EventSEOTests(seo_test_utils.HasSEOAttributesTest):

    #---------------------------------------------------------------------------
    def setUp(self):
        super(EventSEOTests, self).setUp()
        self.resource_type = ResourceType.objects.create(
            key='new_type',
            title = 'New Page Type',
        )
        self.calendar = Calendar.objects.create(
                resource_type=self.resource_type,
                path="/something",
                title="Something Title",
            )

    #---------------------------------------------------------------------------
    def create_resource(self, path):
        return Event.objects.create(
                calendar=self.calendar,
                start_date=datetime.now().date(),
                start_time=datetime.now().time(),
                resource_type=self.resource_type,
                name=path.replace("/", ""),
                title=path,
            )

