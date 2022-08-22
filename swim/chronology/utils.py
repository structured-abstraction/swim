"""
Note: these test are NOT designed to be run alone.
In fact, it is intended that you extend this class and provide
some of the appropriate facilities for it to test your classes
with their date ranges.

In other words, this creates a suite of tests for objects
that extend Timeline.
"""

from datetime import datetime, timedelta, date, time

from django.conf import settings
from django.test import override_settings

from swim.test import TestCase
from swim.event.models import (
    Calendar,
    Event,
)
from swim.chronology import Period, MORNING_KWARGS
from swim.chronology.models import Period as ModelPeriod
from swim.core.models import (
    ResourceType,
    ContentSchema,
    ContentSchemaMember,
)
from swim.content.models import CopySlot, Copy
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class TimelineTests(TestCase):
    """
    Tests which test the appropriate methods of a Timeline object.
    """
    all_timeline_name = ""
    resource_timeline_name = "resource"

    #---------------------------------------------------------------------------
    def setUp(self):
        super(TimelineTests, self).setUp()
        self.OLD_DAY_START_TIME_KWARGS = getattr(settings, 'DAY_START_TIME_KWARGS', None)
        settings.DAY_START_TIME_KWARGS = dict(hour=0, minute=0, second=0)

        self._event_type = ResourceType.objects.create(
                key = 'tng_event',
                title = 'TNG Event',
            )

        self._event_type = ResourceType.objects.create(
                key = 'show',
                title = 'TNG Show',
            )

    #---------------------------------------------------------------------------
    def tearDown(self):
        super(TimelineTests, self).tearDown()
        settings.DAY_START_TIME_KWARGS = self.OLD_DAY_START_TIME_KWARGS

    #---------------------------------------------------------------------------
    def _create_event_range(self, query_set, start_time, end_time):
        return Period(
            query_set,
            start_time,
            end_time,
            self.start_datetime_attr,
            self.end_datetime_attr,
            self.resource_type_attr,
        )

    #---------------------------------------------------------------------------
    def _have_actual_range(self):
        """
        If we don't have a real date range (like for blog posts) then a few
        of the methods don't make a lot of sense.  For instance - it is rare
        that the "now" method makes any sense.  This includes ends_after_now and
        starts_before_now.
        """
        if self.start_datetime_attr == self.end_datetime_attr:
            # If they are the same - then we can't test real ranges.
            # these actually represent instances in time.
            return False
        return True

    #---------------------------------------------------------------------------
    def _test_proper_setup(self):
        if self.__class__ == TimelineTests:
            self.fail(
                "\nIt appears you directly imported TimelineTests " + \
                "into the module namespace for your tests module.  This will " + \
                "cause django to run these tests directly which will not work. " + \
                "please inherit the swim.chronology.tests module like so: \n\n" + \
                "\tfrom swim.chronology import utils as chronology \n" + \
                "\tclass MyTests(chronology.TimelineTests):"
            )


        if getattr(self, '_create_events', None) is None:
            self.fail(
                "Subclasses of TimelineTests must provide a " + \
                "self._create_events which must accept an event list and an " + \
                "optional timeline instance. If no timeline instance is given, use the " + \
                "default timeline instance for these tests. The event list is a list " + \
                "of tuples where each tuple has five elements: " + \
                "event_type, title, start, end."
            )

        if getattr(self, 'timeline', None) is None:
            self.fail(
                "Subclasses of TimelineTests must provide a " + \
                "self.timeline in their setUp method."
            )

        if getattr(self, 'timeline2', None) is None:
            self.fail(
                "Subclasses of TimelineTests must provide a " + \
                "self.timeline2 in their setUp method."
            )

        if getattr(self, 'timeline_event_set', None) is None:
            self.fail(
                "Subclasses of TimelineTests must provide a " + \
                "self.timeline_event_set in their setUp method. This must be a queryset " + \
                "which retrieves all Event objects from the self.timeline."
            )

        if getattr(self, 'start_datetime_attr', None) is None:
            self.fail(
                "Subclasses of TimelineTests must provide a " + \
                "self.start_datetime_attr in their setUp method. This must " + \
                "the name of the attribute on the event objects that contains " + \
                "the start datetime reference."
            )

        if getattr(self, 'end_datetime_attr', None) is None:
            self.fail(
                "Subclasses of TimelineTests must provide a " + \
                "self.end_datetime_attr in their setUp method. This must " + \
                "the name of the attribute on the event objects that contains " + \
                "the start datetime reference."
            )

        if getattr(self, 'resource_type_attr', None) is None:
            self.fail(
                "Subclasses of TimelineTests must provide a " + \
                "self.resource_type_attr in their setUp method. This must " + \
                "the name of the attribute on the event objects that contains " + \
                "the resource_type_reference."
            )

    #---------------------------------------------------------------------------
    def test_timeline_all_method(self):
        self._test_proper_setup()

        # Create a small set of instances for this timeline.
        events = (
                # title, start, end,
                (
                    "tng_event",
                    "event 1",
                    datetime.now() + timedelta(days=-1),
                    datetime.now()
                ),
                (
                    "tng_event",
                    "event 2",
                    datetime.now() + timedelta(days=-4),
                    datetime.now() + timedelta(days=-2)
                ),
                (
                    "tng_event",
                    "event 3",
                    datetime.now() + timedelta(days=-3),
                    datetime.now() + timedelta(days=-3)
                ),
            )
        event_instance_list = self._create_events(events)
        other_timeline_events = (
                (
                    "tng_event",
                    "Some other event 1",
                    datetime.now() + timedelta(days=-1),
                    datetime.now()
                ),
            )
        other_event_instance_list = self._create_events(
                other_timeline_events,
                self.timeline2
            )

        # Create a template that shows them all
        template = Template.objects.create(
                path="/timeline/current_month_view",
                body="""
                    {% for event in """ + self.resource_timeline_name + """.all.events %}
                        {{ event.url }}
                    {% endfor %}
                """
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order = 0,
            resource_type = self.timeline_resource_type,
            template = template
        )

        # the .all method on a timeline MUST return ALL of the events it contains.
        response = self.client.get(self.timeline.url())
        self.assertEqual(response.status_code, 200)
        for event in event_instance_list:
            self.assertIn(event.url(), response.content)

        # None of the other timeline events will be in this view.
        for event in other_event_instance_list:
            self.assertNotIn(event.url(), response.content)

        template.body = """
                    {% for event in """ + self.all_timeline_name + """.all.events %}
                        {{ event.url }}
                    {% endfor %}
        """
        template.save()
        # In this case ALL of the events MUST Be there.
        response = self.client.get(self.timeline.url())
        self.assertEqual(response.status_code, 200)
        for event in event_instance_list + other_event_instance_list:
            self.assertIn(event.url(), response.content)

    #---------------------------------------------------------------------------
    def _create_now_instances(self, timeline):
        """
        Create a set of events that are happening right now.
        """
        now_events = (
                ("tng_event", "now event 1 %s" % timeline.title,
                    datetime.now(),
                    datetime.now() + timedelta(minutes=10),),
                ("tng_event", "now event 2 %s" % timeline.title,
                    datetime.now() + timedelta(minutes=-4),
                    datetime.now() + timedelta(minutes=2)),
            )
        return self._create_events(now_events, timeline)

    #---------------------------------------------------------------------------
    def _create_ends_before_now_instances(self, timeline):
        """
        Create a set of events that are not happening in the starts_after_now
        """
        not_now_events = (
                # A starts_after_now event
                ("tng_event", "ends_before_now event 1 %s" % timeline.title,
                    datetime.now() + timedelta(minutes=-15),
                    datetime.now() + timedelta(minutes=-15),),

                # A ends_before_now event
                ("tng_event", "ends_before_now event 2 %s"%timeline.title,
                    datetime.now() + timedelta(minutes=-4),
                    datetime.now() + timedelta(minutes=-2)),
            )
        return self._create_events(not_now_events, timeline)

    #---------------------------------------------------------------------------
    def _create_starts_after_now_instances(self, timeline):
        """
        Create a set of events that are not happening in the starts_after_now
        """
        not_now_events = (
                # A starts_after_now event
                ("tng_event", "starts_after_now event 1 %s" % timeline.title,
                    datetime.now() + timedelta(minutes=9),
                    datetime.now() + timedelta(minutes=10),),

                # A ends_before_now event
                ("tng_event", "starts_after_now event 2 %s"%timeline.title ,
                    datetime.now() + timedelta(minutes=2),
                    datetime.now() + timedelta(minutes=5)),
            )
        return self._create_events(not_now_events, timeline)

    #---------------------------------------------------------------------------
    def _create_not_now_instances(self, timeline):
        """
        Create a set of events that are not happening right now.
        """
        not_now_events = (
                # A starts_after_now event
                ("tng_event", "not now event 1 %s" % timeline.title,
                    datetime.now() + timedelta(minutes=9),
                    datetime.now() + timedelta(minutes=10),),

                # A ends_before_now event
                ("tng_event", "not now event 2 %s"%timeline.title,
                    datetime.now() + timedelta(minutes=-4),
                    datetime.now() + timedelta(minutes=-2)),
            )
        return self._create_events(not_now_events, timeline)

    #---------------------------------------------------------------------------
    def _create_not_scheduled_instances(self, timeline):
        """
        Create a set of events that are not scheduled
        """
        not_scheduled_events = (
                # A ends_before_now event
                ("tng_event", "not scheduled event 2 %s"%timeline.title ,
                    None,
                    None,),
            )
        return self._create_events(not_scheduled_events, timeline)

    #---------------------------------------------------------------------------
    def _run_timeline_test(self, test_cases):
        # Create a template that shows the ones happening right now
        template = Template.objects.create(
                path="/timeline/current_month_view",
                body="""
                """
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order = 0,
            resource_type = self.timeline_resource_type,
            template = template
        )

        for body, included_instances, excluded_instances in test_cases:
            # Create a template that shows only the ones for today.
            template.body = body
            template.save()

            # the .all method on a timeline MUST return ALL of the events it contains.
            response = self.client.get(self.timeline.url())
            self.assertEqual(response.status_code, 200)
            for event in included_instances:
                self.assertIn(event.url(), response.content)

            for event in excluded_instances:
                self.assertNotIn(event.url(), response.content)

    #---------------------------------------------------------------------------
    def test_timeline_restrict_by_type_and_indexing(self):
        self._test_proper_setup()

        # Inspired by a bug we had in TNG.
        # Test that after restricting by type, we can still index the
        # range properly:
        starts_after_now_event_list = self._create_starts_after_now_instances(self.timeline)
        ends_before_now_event_list = self._create_ends_before_now_instances(self.timeline)
        other_event_instance_list = self._create_starts_after_now_instances(self.timeline2)


        # Test the indexing works
        # Strangely, the create_now_instances doesn't return a
        # date ordered list, so the first event in the list it returns
        # is actually the second event in date order.
        test_cases = (
                # body, included_instances, excluded_instances
                (
                    """
                    {{ """ + self.resource_timeline_name + """.starts_after_now.tng_event.events.1.url }}
                    """,
                    starts_after_now_event_list[:1],
                    starts_after_now_event_list[1:] + ends_before_now_event_list + other_event_instance_list,
                ),

            )
        self._run_timeline_test(test_cases)

    #---------------------------------------------------------------------------
    def test_timeline_now_methods(self):
        self._test_proper_setup()
        if not self._have_actual_range(): return

        now_event_list = self._create_now_instances(self.timeline)
        not_now_event_list = self._create_not_now_instances(self.timeline)
        other_event_instance_list = self._create_now_instances(self.timeline2)


        test_cases = (
                # body, included_instances, excluded_instances
                (
                    """
                    {% for event in """ + self.resource_timeline_name + """.now.events %}
                        {{ event.url }}
                    {% endfor %}
                    """,
                    now_event_list,
                    not_now_event_list + other_event_instance_list,
                ),
                (
                    """
                    {% for event in """ + self.resource_timeline_name + """.now.days.0.events %}
                        {{ event.url }}
                    {% endfor %}
                    """,
                    now_event_list + not_now_event_list,
                    other_event_instance_list,
                ),
                (
                    """
                    {% for event in """ + self.all_timeline_name + """.now.events %}
                        {{ event.url }}
                    {% endfor %}
                    """,
                    now_event_list + other_event_instance_list,
                    not_now_event_list,
                ),

            )
        self._run_timeline_test(test_cases)


    #---------------------------------------------------------------------------
    def test_timeline_ends_after_now_method(self):
        self._test_proper_setup()
        if not self._have_actual_range(): return

        now_event_list = self._create_now_instances(self.timeline)
        starts_after_now_instances = self._create_starts_after_now_instances(self.timeline)
        ends_before_now_instances = self._create_ends_before_now_instances(self.timeline)
        other_event_instance_list = self._create_now_instances(self.timeline2)
        other_starts_after_now_event_instances = self._create_starts_after_now_instances(self.timeline2)

        test_cases = (
                # body, included_instances, excluded_instances
                (
                    """
                    {% for event in """ + self.resource_timeline_name + """.ends_after_now.events %}
                        {{ event.url }}
                    {% endfor %}
                    """,
                    now_event_list + starts_after_now_instances,
                    ends_before_now_instances + other_event_instance_list + other_starts_after_now_event_instances,
                ),
                (
                    """
                    {% for event in """ + self.all_timeline_name + """.ends_after_now.events %}
                        {{ event.url }}
                    {% endfor %}
                    """,
                    now_event_list + starts_after_now_instances + other_event_instance_list + other_starts_after_now_event_instances,
                    ends_before_now_instances,
                ),

            )
        self._run_timeline_test(test_cases)

    #---------------------------------------------------------------------------
    def test_timeline_starts_before_now_method(self):
        self._test_proper_setup()

        now_event_list = self._create_now_instances(self.timeline)
        starts_after_now_instances = self._create_starts_after_now_instances(self.timeline)
        ends_before_now_instances = self._create_ends_before_now_instances(self.timeline)
        other_event_instance_list = self._create_now_instances(self.timeline2)
        other_ends_before_now_event_instance_list = self._create_ends_before_now_instances(self.timeline2)

        test_cases = (
                # body, included_instances, excluded_instances
                (
                    """
                    {% for event in """ + self.resource_timeline_name + """.starts_before_now.events %}
                        {{ event.url }}
                    {% endfor %}
                    """,
                    now_event_list + ends_before_now_instances,
                    starts_after_now_instances + other_event_instance_list + other_ends_before_now_event_instance_list,
                ),
                (
                    """
                    {% for event in """ + self.all_timeline_name + """.starts_before_now.events %}
                        {{ event.url }}
                    {% endfor %}
                    """,
                    now_event_list + ends_before_now_instances + other_event_instance_list + other_ends_before_now_event_instance_list,
                    starts_after_now_instances,
                ),

            )
        self._run_timeline_test(test_cases)

    #---------------------------------------------------------------------------
    def test_timeline_starts_after_now_method(self):
        self._test_proper_setup()

        # Create a small set of instances for this timeline.
        ends_before_now_events = (
                # title, start, end,
                # An event completely in the ends_before_now SHOULD NOT be in there
                ("tng_event", "event 1",
                    datetime.now() + timedelta(minutes=-10),
                    datetime.now() + timedelta(minutes=-5),),
                # An event that starts in the ends_before_now SHOULD NOT be in there
                ("tng_event", "event 2",
                    datetime.now() + timedelta(minutes=-4),
                    datetime.now() + timedelta(minutes=2)),
            )
        ends_before_now_event_instance_list = self._create_events(ends_before_now_events)
        starts_after_now_events = (
                # title, start, end,
                # only starts_after_now events should be there.
                ("tng_event", "event 3",
                    datetime.now() + timedelta(minutes=9),
                    datetime.now() + timedelta(minutes=10),),
                ("tng_event", "event 4",
                    datetime.now() + timedelta(minutes=4),
                    datetime.now() + timedelta(minutes=5)),
                ("tng_event", "event 6",
                    datetime.now() + timedelta(days=4),
                    None),
            )
        starts_after_now_event_instance_list = self._create_events(starts_after_now_events)
        other_timeline_starts_after_now_events = (
                ("tng_event", "Main Space event 1",
                    datetime.now() + timedelta(days=1),
                    datetime.now() + timedelta(days=2)),
                ("tng_event", "main space event 6",
                    datetime.now() + timedelta(days=4),
                    None),
            )
        other_event_instance_list = self._create_events(
                other_timeline_starts_after_now_events,
                self.timeline2
            )

        # Create a template that shows the ones happening right now
        template = Template.objects.create(
                path="/timeline/current_month_view",
                body="""
                    {% for event in """ + self.resource_timeline_name + """.starts_after_now.events %}
                        {{ event.url }}
                    {% endfor %}
                """
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order = 0,
            resource_type = self.timeline_resource_type,
            template = template
        )

        # the .all method on a timeline MUST return ALL of the events it contains.
        response = self.client.get(self.timeline.url())
        self.assertEqual(response.status_code, 200)
        for event in ends_before_now_event_instance_list:
            self.assertNotIn(event.url(), response.content)

        # the .all method on a timeline MUST return ALL of the events it contains.
        for event in starts_after_now_event_instance_list:
            self.assertIn(event.url(), response.content)

        # None of the other timeline events will be in this view.
        for event in other_event_instance_list:
            self.assertNotIn(event.url(), response.content)

        # ALL of the starts_after_now events should be in this view
        template.body = """
                    {% for event in """ + self.all_timeline_name + """.starts_after_now.events %}
                        {{ event.url }}
                    {% endfor %}
        """
        template.save()

        # In this case ALL of the events MUST Be there.
        response = self.client.get(self.timeline.url())
        self.assertEqual(response.status_code, 200)
        for event in starts_after_now_event_instance_list + other_event_instance_list:
            self.assertIn(event.url(), response.content)


    #---------------------------------------------------------------------------
    def test_timeline_ends_before_now_method(self):
        self._test_proper_setup()

        # Create a small set of instances for this timeline.
        starts_after_now_events = (
                # title, start, end,
                # An event completely in the starts_after_now SHOULD NOT be in there
                ("tng_event", "event 1",
                    datetime.now() + timedelta(minutes=10),
                    datetime.now() + timedelta(minutes=15),),
            )
        starts_after_now_event_instance_list = self._create_events(starts_after_now_events)
        concurrent_events = (
                # An event that ends in the starts_after_now SHOULD NOT be in there
                ("tng_event", "event 2",
                    datetime.now() + timedelta(minutes=-4),
                    datetime.now() + timedelta(minutes=2)),
            )
        concurrent_event_instance_list = self._create_events(concurrent_events)
        ends_before_now_events = (
                # title, start, end,
                # ends_before_now events SHOULD NOT BE there
                ("tng_event", "event 3",
                    datetime.now() + timedelta(minutes=-19),
                    datetime.now() + timedelta(minutes=-10),),
                ("tng_event", "event 4",
                    datetime.now() + timedelta(minutes=-14),
                    datetime.now() + timedelta(minutes=-5)),
            )
        ends_before_now_event_instance_list = self._create_events(ends_before_now_events)
        other_timeline_ends_before_now_events = (
                ("tng_event", "Main Space event 1",
                    datetime.now() + timedelta(days=-2),
                    datetime.now() + timedelta(days=-1)),
            )
        other_event_instance_list = self._create_events(
                other_timeline_ends_before_now_events,
                self.timeline2
            )


        # Create a template that shows the ones happening right now
        template = Template.objects.create(
                path="/timeline/current_month_view",
                body="""
                    {% for event in """ + self.resource_timeline_name + """.ends_before_now.events %}
                        {{ event.url }}
                    {% endfor %}
                """
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order = 0,
            resource_type = self.timeline_resource_type,
            template = template
        )

        # the .all method on a timeline MUST return ALL of the events it contains.
        response = self.client.get(self.timeline.url())
        self.assertEqual(response.status_code, 200)
        for event in starts_after_now_event_instance_list:
            self.assertNotIn(event.url(), response.content)

        if self._have_actual_range():
            response = self.client.get(self.timeline.url())
            self.assertEqual(response.status_code, 200)
            for event in concurrent_event_instance_list:
                self.assertNotIn(event.url(), response.content)

        # the .all method on a timeline MUST return ALL of the events it contains.
        for event in ends_before_now_event_instance_list:
            self.assertIn(event.url(), response.content)

        # None of the other timeline events will be in this view.
        for event in other_event_instance_list:
            self.assertNotIn(event.url(), response.content)

        # ALL of the starts_after_now events should be in this view
        template.body = """
                    {% for event in """ + self.all_timeline_name + """.ends_before_now.events %}
                        {{ event.url }}
                    {% endfor %}
        """
        template.save()

        # In this case ALL of the events MUST Be there.
        response = self.client.get(self.timeline.url())
        self.assertEqual(response.status_code, 200)
        for event in ends_before_now_event_instance_list + other_event_instance_list:
            self.assertIn(event.url(), response.content)

    #---------------------------------------------------------------------------
    def test_timeline_mixing_range_splitting_and_period_methods(self):
        self._test_proper_setup()

        # Create a small set of instances for this timeline.
        ends_before_now_events = (
                # title, start, end,
                # An event completely in the ends_before_now SHOULD NOT be in there
                ("tng_event", "event 1",
                    datetime.now() + timedelta(minutes=-10),
                    datetime.now() + timedelta(minutes=-5),),
                # An event that starts in the ends_before_now SHOULD NOT be in there
                ("tng_event", "event 2",
                    datetime.now() + timedelta(minutes=-4),
                    datetime.now() + timedelta(minutes=2)),
            )
        ends_before_now_event_instance_list = self._create_events(ends_before_now_events)

        # Create a template that shows the ones happening right now
        template = Template.objects.create(
                path="/timeline/current_month_view",
                body="""
                    {% for week in """ + self.resource_timeline_name + """.weeks %}
                        {% for event in week.starts_before_now.events %}
                            {{ event.url }}
                        {% endfor %}
                    {% endfor %}
                """
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order = 0,
            resource_type = self.timeline_resource_type,
            template = template
        )

        # the .all method on a timeline MUST return ALL of the events it contains.
        response = self.client.get(self.timeline.url())
        self.assertEqual(response.status_code, 200)
        for event in ends_before_now_event_instance_list:
            self.assertIn(event.url(), response.content)


    #---------------------------------------------------------------------------
    def test_timeline_starts_after_now_date_range_includes_now(self):
        self._test_proper_setup()
        if not self._have_actual_range(): return

        # Setup a specific situation (TNG inspired):
        # 3 events, one spans new years, one starts in the new year, and one
        # ends in the old year.  Do this for a ends_before_now year.
        # When looping over the ends_before_now events in the new year we should see
        # 2 of the events
        completely_ends_before_now_events = (
                ("tng_event", "event 1", datetime(2007,12,21), datetime(2007, 12, 31)),
            )
        ends_before_now_event_instance_list = self._create_events(completely_ends_before_now_events)
        completely_starts_after_now_events = (
                ("tng_event", "event 3", datetime(2008,1,2), datetime(2008, 1, 10)),
            )
        starts_after_now_event_instance_list = self._create_events(completely_starts_after_now_events)

        now_events = (
                ("tng_event", "event 4", datetime(2007,12,28), datetime(2008, 1, 10)),
            )
        now_event_instance_list = self._create_events(now_events)
        # Create a template that shows the events happening
        template = Template.objects.create(
                path="/timeline/testing_something_mofos",
                body="""
                {% for event in """ + self.resource_timeline_name + """.ends_before_now.years.1.events %}
                    {{ event.start_date|date:"Y-m-d" }}
                    {{ event.end_date|date:"Y-m-d" }}
                    {{ event.url }}
                {% endfor %}
                """
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order = 0,
            resource_type = self.timeline_resource_type,
            template = template
        )

        response = self.client.get(self.timeline.url())
        self.assertEqual(response.status_code, 200)

        for event in starts_after_now_event_instance_list + now_event_instance_list:
            self.assertIn(event.url(), response.content)

    #---------------------------------------------------------------------------
    def test_timeline_ranges_queries_respect_null_dates(self):
        self._test_proper_setup()

        # Setup a specific situation (TNG inspired):
        # An event with a start_date, but no end date, and vice versa
        #
        # For both cases where the date is specified if the date is within
        # our range then the events should be included.
        #
        # For the cases where the date is specified, the but it is outside
        # of our given range, then we should exclude them.
        #
        # For the cases where neither a start or end date is specified they
        # should be excluded.
        events_not_included = (
                ("tng_event", "event 1", datetime(2007,12,21), datetime(2007, 12, 31)),
                ("tng_event", "event 2", datetime(2007,12,21), None),
            )
        events_not_included_instances = self._create_events(events_not_included)
        events_included = (
                ("tng_event", "event 5", datetime(2008,1,2), None),
            )
        events_included_instances = self._create_events(events_included)

        # Create a template that shows the events happening in the second year
        # of all our ends_before_now years with the above data, that's 2008
        template = Template.objects.create(
                path="/timeline/testing_something_mofos",
                body="""
                {% for event in """ + self.resource_timeline_name + """.ends_before_now.years.1.events %}
                    {{ event.start_date|date:"Y-m-d" }}
                    {{ event.end_date|date:"Y-m-d" }}
                    {{ event.url }}
                {% endfor %}
                """
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order = 0,
            resource_type = self.timeline_resource_type,
            template = template
        )

        response = self.client.get(self.timeline.url())
        self.assertEqual(response.status_code, 200)

        for event in events_included_instances:
            self.assertIn(event.url(), response.content)

        for event in events_not_included_instances:
            self.assertNotIn(event.url(), response.content)

    #---------------------------------------------------------------------------
    def test_timeline_ranges_that_are_large_return_everything(self):
        self._test_proper_setup()

        # Setup a specific situation (TNG inspired):
        # There are events that start in the starts_after_now, but there are events
        # that started in the ends_before_now that end in the starts_after_now (In fact they end
        # after the starts_after_now events start, and there are events that started
        # in the ends_before_now and end in the ends_before_now.
        #
        # In the case however, that we use a date range that is large enough
        # (say a millenium) - then ALL the event should show up regardless of
        #  whether we start with .starts_after_now, .now or .ends_before_now
        # The following test uses a millenium and may stop working for a few
        # weeks in December 2999, and start working again a few weeks into
        # January 3000
        completely_ends_before_now_events = (
                ("tng_event", "event 1",
                    datetime.now() + timedelta(days=-5),
                    datetime.now() + timedelta(days=-2),),
            )
        ends_before_now_event_instance_list = self._create_events(completely_ends_before_now_events)
        completely_starts_after_now_events = (
                # title, start, end,
                # only starts_after_now events should be there.
                ("tng_event", "event 3",
                    datetime.now() + timedelta(days=1),
                    datetime.now() + timedelta(days=10),),
            )
        starts_after_now_event_instance_list = self._create_events(completely_starts_after_now_events)

        now_events = (
                # title, start, end,
                # only starts_after_now events should be there.
                ("tng_event", "event 4",
                    datetime.now() + timedelta(days=-1),
                    datetime.now() + timedelta(days=7),),
            )
        now_event_instance_list = self._create_events(now_events)

        # Create a template that shows the events happening
        template = Template.objects.create(
                path="/timeline/testing_something_mofos",
                body="""
                """
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order = 0,
            resource_type = self.timeline_resource_type,
            template = template
        )
        test_cases = (
            """
                {% for millenia in """ + self.resource_timeline_name + """.ends_before_now.millenia %}
                    {% for event in millenia.events %}
                        {{ event.url }}
                    {% endfor %}
                {% endfor %}
            """,
            """
                {% for millenia in """ + self.resource_timeline_name + """.now.millenia %}
                    {% for event in millenia.events %}
                        {{ event.url }}
                    {% endfor %}
                {% endfor %}
            """,
            """
                {% for millenia in """ + self.resource_timeline_name + """.starts_after_now.millenia %}
                    {% for event in millenia.events %}
                        {{ event.url }}
                    {% endfor %}
                {% endfor %}
            """,
        )
        all_event_instances = (
                ends_before_now_event_instance_list +
                now_event_instance_list +
                starts_after_now_event_instance_list
            )

        # Because of the large range of time that we use ALL of the
        # events MUST be included in each of the test_cases.
        for body in test_cases:
            template.body = body
            template.save()

            response = self.client.get(self.timeline.url())
            self.assertEqual(response.status_code, 200)

            for event in all_event_instances:
                self.assertIn(event.url(), response.content)

    #---------------------------------------------------------------------------
    def test_timeline_restrict_by_type(self):
        self._test_proper_setup()

        # Create a small set of instances for this timeline.
        events = (
                # type_key, title, start, end,
                ("tng_event", "event 1",
                    datetime.now() + timedelta(days=-1),
                    datetime.now()),
                ("tng_event", "event 2",
                    datetime.now() + timedelta(days=-4),
                    datetime.now() + timedelta(days=-2)),
                ("tng_event", "event 3",
                    datetime.now() + timedelta(days=-3),
                    None,),
            )
        event_instance_list = self._create_events(events)
        shows = (
                ("show", "show 1",
                    datetime.now() + timedelta(days=-3),
                    datetime.now() + timedelta(days=-3)),
            )
        show_instance_list = self._create_events(shows)

        test_cases = (
                # body, included_instances, excluded_instances
                (
                    """
                        {% for event in """ + self.resource_timeline_name + """.all.tng_event.events %}
                            {{ event.url }}
                        {% endfor %}
                    """,
                    # the .<type> method on a Period MUST return
                    # ALL of the events of that type.
                    # In this case ALL events must be included and ALL
                    # shows must be excluded.
                    event_instance_list,
                    show_instance_list,
                ),
                (
                    """
                        {% for show in """ + self.resource_timeline_name + """.all.show.events %}
                            {{ show.url }}
                        {% endfor %}
                    """,
                    # the .<type> method on a Period MUST return
                    # ALL of the events of that type.
                    # In this case ALL events must be excluded and ALL
                    # shows must be included.
                    show_instance_list,
                    event_instance_list
                ),
                (
                    """
                        {% for show in """ + self.resource_timeline_name + """.all.all_types.events %}
                            {{ show.url }}
                        {% endfor %}
                    """,
                    # the .<type> method on a Period MUST return
                    # ALL of the events of that type.
                    # In this case ALL events must be included and ALL
                    # shows must be included.
                    show_instance_list + event_instance_list,
                    [],
                ),
                (
                    """
                        {% for day in """ + self.resource_timeline_name + """.all.show.days %}
                            {% for event in day.millenia.0.all_types.events %}
                                {{ event.url }}
                            {% endfor %}
                        {% endfor %}
                    """,
                    show_instance_list + event_instance_list,
                    [],
                ),
                (
                    """
                        {% for day in """ + self.resource_timeline_name + """.all.tng_event.days %}
                            {% for show in day.all_types.events %}
                                {{ show.url }}
                            {% endfor %}
                        {% endfor %}
                    """,
                    event_instance_list + show_instance_list,
                    [],
                ),

            )
        self._run_timeline_test(test_cases)



    #---------------------------------------------------------------------------
    def test_timeline_range_second_split(self):
        self._test_proper_setup()

        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2007, 1, 1, 10, 1, 4),
                datetime(2007, 1, 1, 10, 1, 7),
            )
        second_ranges = initial_range.seconds()
        self.assertEqual(len(second_ranges), 4)
        for expected_second, second_range in zip(range(4,8), second_ranges):
            self.assertEqual(time(10,1,expected_second), second_range.start_date.time())
            self.assertEqual(time(10,1,expected_second), second_range.end_date.time())


    #---------------------------------------------------------------------------
    def test_timeline_range_minute_split(self):
        self._test_proper_setup()

        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2007, 1, 1, 10, 1, 0),
                datetime(2007, 1, 1, 10, 3, 0),
            )
        minute_ranges = initial_range.minutes()
        self.assertEqual(len(minute_ranges), 3)
        for expected_minute, minute_range in zip(range(1,4), minute_ranges):
            self.assertEqual(time(10,expected_minute,0), minute_range.start_date.time())
            self.assertEqual(time(10,expected_minute,59), minute_range.end_date.time())

        # Test a range that crosses a hour
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2007, 1, 1, 1, 59, 0),
                datetime(2007, 1, 1, 2, 1, 0),
            )
        minute_ranges = initial_range.minutes()
        self.assertEqual(len(minute_ranges), 3)
        for expected_hour, expected_minute, minute_range in zip([1,2,2], [59,0,1], minute_ranges):
            self.assertEqual(time(expected_hour, expected_minute,0), minute_range.start_date.time())
            self.assertEqual(time(expected_hour, expected_minute,59), minute_range.end_date.time())


        # Test a range that is smaller than an minute and doesn't cross an minute
        # boundary
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2007, 1, 1, 10, 10, 10),
                datetime(2007, 1, 1, 10, 10, 20),
            )
        minute_ranges = initial_range.minutes()
        self.assertEqual(len(minute_ranges), 1)
        for expected_minute, minute_range in zip([10], minute_ranges):
            self.assertEqual(time(10, expected_minute,0), minute_range.start_date.time())
            self.assertEqual(time(10, expected_minute,59), minute_range.end_date.time())

        # Test a range that is smaller than an minute and does cross an minute
        # boundary
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2007, 1, 1, 10, 10, 59),
                datetime(2007, 1, 1, 10, 11, 1),
            )
        minute_ranges = initial_range.minutes()
        self.assertEqual(len(minute_ranges), 2)
        for expected_minute, minute_range in zip([10,11], minute_ranges):
            self.assertEqual(time(10, expected_minute,0), minute_range.start_date.time())
            self.assertEqual(time(10, expected_minute,59), minute_range.end_date.time())

    #---------------------------------------------------------------------------
    def test_timeline_range_hour_split(self):
        self._test_proper_setup()

        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2007, 1, 1, 10, 0, 0),
                datetime(2007, 1, 1, 12, 0, 0),
            )
        hour_ranges = initial_range.hours()
        self.assertEqual(len(hour_ranges), 3)
        for expected_hour, hour_range in zip(range(10,13), hour_ranges):
            self.assertEqual(time(expected_hour,0,0), hour_range.start_date.time())
            self.assertEqual(time(expected_hour,59,59), hour_range.end_date.time())

        # Test a range that crosses a day
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2007, 1, 1, 23, 0, 0),
                datetime(2007, 1, 2, 1, 0, 0),
            )
        hour_ranges = initial_range.hours()
        self.assertEqual(len(hour_ranges), 3)
        for expected_hour, hour_range in zip([23,0,1], hour_ranges):
            self.assertEqual(time(expected_hour,0,0), hour_range.start_date.time())
            self.assertEqual(time(expected_hour,59,59), hour_range.end_date.time())


        # Test a range that is smaller than an hour and doesn't cross an hour
        # boundary
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2007, 1, 1, 10, 10, 0),
                datetime(2007, 1, 1, 10, 20, 0),
            )
        hour_ranges = initial_range.hours()
        self.assertEqual(len(hour_ranges), 1)
        for expected_hour, hour_range in zip([10], hour_ranges):
            self.assertEqual(time(expected_hour,0,0), hour_range.start_date.time())
            self.assertEqual(time(expected_hour,59,59), hour_range.end_date.time())

        # Test a range that is smaller than an hour and does cross an hour
        # boundary
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2007, 1, 1, 10, 50, 0),
                datetime(2007, 1, 1, 11, 10, 0),
            )
        hour_ranges = initial_range.hours()
        self.assertEqual(len(hour_ranges), 2)
        for expected_hour, hour_range in zip([10,11], hour_ranges):
            self.assertEqual(time(expected_hour,0,0), hour_range.start_date.time())
            self.assertEqual(time(expected_hour,59,59), hour_range.end_date.time())


    #---------------------------------------------------------------------------
    def test_timeline_range_day_split(self):
        self._test_proper_setup()

        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2007, 1, 1),
                datetime(2007, 1, 10),
            )
        day_ranges = initial_range.days()
        self.assertEqual(len(day_ranges), 10)
        for expected_day, day_range in zip(range(1,11), day_ranges):
            self.assertEqual(expected_day, day_range.start_date.day)
            self.assertEqual(time(0,0,0), day_range.start_date.time())

            self.assertEqual(expected_day, day_range.end_date.day)
            self.assertEqual(time(23,59,59), day_range.end_date.time())

        # Test leap years over February
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2000, 2, 28),
                datetime(2000, 3, 1),
            )
        day_ranges = initial_range.days()
        self.assertEqual(len(day_ranges), 3)
        for expected_day, expected_month, day_range in zip([28,29,1], [2,2,3], day_ranges):
            self.assertEqual(expected_day, day_range.start_date.day)
            self.assertEqual(time(0,0,0), day_range.start_date.time())

            self.assertEqual(expected_day, day_range.end_date.day)
            self.assertEqual(time(23,59,59), day_range.end_date.time())

        # Test non leap years in February
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2001, 2, 28),
                datetime(2001, 3, 1),
            )
        day_ranges = initial_range.days()
        self.assertEqual(len(day_ranges), 2)
        for expected_day, expected_month, day_range in zip([28,1], [2,3], day_ranges):
            self.assertEqual(expected_day, day_range.start_date.day)
            self.assertEqual(time(0,0,0), day_range.start_date.time())

            self.assertEqual(expected_day, day_range.end_date.day)
            self.assertEqual(time(23,59,59), day_range.end_date.time())

        # Test ranges that are smaller than a day
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2001, 1, 1, 10, 20, 0),
                datetime(2001, 1, 1, 10, 21, 0),
            )
        day_ranges = initial_range.days()
        self.assertEqual(len(day_ranges), 1)
        for expected_day, expected_month, day_range in zip([1,], [1,], day_ranges):
            self.assertEqual(expected_day, day_range.start_date.day)
            self.assertEqual(time(0,0,0), day_range.start_date.time())

            self.assertEqual(expected_day, day_range.end_date.day)
            self.assertEqual(time(23,59,59), day_range.end_date.time())

    #---------------------------------------------------------------------------
    def test_timeline_range_day_split_with_custom_start_times(self):
        self._test_proper_setup()
        from django.conf import settings
        settings.DAY_START_TIME_KWARGS = dict(hour=4, minute=0, second=0)
        try:
            initial_range = self._create_event_range(
                    self.timeline_event_set.all(),
                    datetime(2007, 1, 1),
                    datetime(2007, 1, 10),
                )
            day_ranges = initial_range.days()
            self.assertEqual(len(day_ranges), 10)
            expected = zip(range(1,11), range(2,12), day_ranges)
            for expected_start_day, expected_end_day, day_range in expected:
                self.assertEqual(expected_start_day, day_range.start_date.day)
                self.assertEqual(time(4,0,0), day_range.start_date.time())

                self.assertEqual(expected_end_day, day_range.end_date.day)
                self.assertEqual(time(3,59,59), day_range.end_date.time())

            # Test leap years over February
            initial_range = self._create_event_range(
                    self.timeline_event_set.all(),
                    datetime(2000, 2, 28),
                    datetime(2000, 3, 1),
                )
            day_ranges = initial_range.days()
            self.assertEqual(len(day_ranges), 3)

            expected = zip([28,29,1], [29, 1, 2], [2,2,3], day_ranges)
            for expected_start_day, expected_end_day, expected_month, day_range in expected:
                self.assertEqual(expected_start_day, day_range.start_date.day)
                self.assertEqual(time(4,0,0), day_range.start_date.time())

                self.assertEqual(expected_end_day, day_range.end_date.day)
                self.assertEqual(time(3,59,59), day_range.end_date.time())

            # Test non leap years in February
            initial_range = self._create_event_range(
                    self.timeline_event_set.all(),
                    datetime(2001, 2, 28),
                    datetime(2001, 3, 1),
                )
            day_ranges = initial_range.days()
            self.assertEqual(len(day_ranges), 2)
            expected = zip([28,1], [1, 2], [2,3], day_ranges)
            for expected_start_day, expected_end_day, expected_month, day_range in expected:
                self.assertEqual(expected_start_day, day_range.start_date.day)
                self.assertEqual(time(4,0,0), day_range.start_date.time())

                self.assertEqual(expected_end_day, day_range.end_date.day)
                self.assertEqual(time(3,59,59), day_range.end_date.time())

            # Test ranges that are smaller than a day
            initial_range = self._create_event_range(
                    self.timeline_event_set.all(),
                    datetime(2001, 1, 1, 10, 20, 0),
                    datetime(2001, 1, 1, 10, 21, 0),
                )
            day_ranges = initial_range.days()
            self.assertEqual(len(day_ranges), 1)
            expected = zip([1,], [2,], [1,], day_ranges)
            for expected_start_day, expected_end_day, expected_month, day_range in expected:
                self.assertEqual(expected_start_day, day_range.start_date.day)
                self.assertEqual(time(4,0,0), day_range.start_date.time())

                self.assertEqual(expected_end_day, day_range.end_date.day)
                self.assertEqual(time(3,59,59), day_range.end_date.time())
        finally:
            settings.DAY_START_TIME_KWARGS = MORNING_KWARGS

    #---------------------------------------------------------------------------
    def _test_ranges(self, generated_ranges, expected_ranges):
        self.assertEqual(len(generated_ranges), len(expected_ranges))
        for expected_range, generated_range in zip(expected_ranges, generated_ranges):
            self.assertEqual(expected_range[0], generated_range.start_date)
            self.assertEqual(expected_range[1], generated_range.end_date)

    #---------------------------------------------------------------------------
    def test_timeline_range_week_split(self):
        self._test_proper_setup()

        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2006, 1, 1),
                datetime(2006, 1, 31),
            )
        expected_ranges = (
            # start_datetime, end_datetime
            (datetime(2005, 12, 26, 0, 0, 0), datetime(2006, 1,  1, 23, 59, 59)),
            (datetime(2006,  1,  2, 0, 0, 0), datetime(2006, 1,  8, 23, 59, 59)),
            (datetime(2006,  1,  9, 0, 0, 0), datetime(2006, 1, 15, 23, 59, 59)),
            (datetime(2006,  1, 16, 0, 0, 0), datetime(2006, 1, 22, 23, 59, 59)),
            (datetime(2006,  1, 23, 0, 0, 0), datetime(2006, 1, 29, 23, 59, 59)),
            (datetime(2006,  1, 30, 0, 0, 0), datetime(2006, 2,  5, 23, 59, 59)),
        )
        week_ranges = initial_range.weeks()
        self._test_ranges(week_ranges, expected_ranges)
        week_ranges = initial_range.monday_weeks()
        self._test_ranges(week_ranges, expected_ranges)

        # Test ranges that are smaller than a week within one week
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2006, 1, 2),
                datetime(2006, 1, 4),
            )
        expected_ranges = (
            (datetime(2006,1,2,0,0,0), datetime(2006,1,8,23,59,59)),
        )
        week_ranges = initial_range.weeks()
        self._test_ranges(week_ranges, expected_ranges)
        week_ranges = initial_range.monday_weeks()
        self._test_ranges(week_ranges, expected_ranges)

        # Test ranges that are smaller than a week but span two weeks
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2006, 1, 7),
                datetime(2006, 1, 9),
            )
        expected_ranges =(
            (datetime(2006,1,2,0,0,0), datetime(2006,1,8,23,59,59)),
            (datetime(2006,1,9,0,0,0), datetime(2006,1,15,23,59,59)),
        )
        week_ranges = initial_range.weeks()
        self._test_ranges(week_ranges, expected_ranges)
        week_ranges = initial_range.monday_weeks()
        self._test_ranges(week_ranges, expected_ranges)

    #---------------------------------------------------------------------------
    def test_timeline_range_sunday_week_split(self):
        self._test_proper_setup()

        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2009, 2, 1),
                datetime(2009, 2, 28),
            )
        expected_ranges = (
            # start_datetime, end_datetime
            (datetime(2009,  2,  1, 0, 0, 0), datetime(2009, 2,  7, 23, 59, 59)),
            (datetime(2009,  2,  8, 0, 0, 0), datetime(2009, 2, 14, 23, 59, 59)),
            (datetime(2009,  2, 15, 0, 0, 0), datetime(2009, 2, 21, 23, 59, 59)),
            (datetime(2009,  2, 22, 0, 0, 0), datetime(2009, 2, 28, 23, 59, 59)),
        )
        week_ranges = initial_range.sunday_weeks()
        self._test_ranges(week_ranges, expected_ranges)

        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2006, 1, 1),
                datetime(2006, 1, 31),
            )
        expected_ranges = (
            # start_datetime, end_datetime
            (datetime(2006,  1,  1, 0, 0, 0), datetime(2006, 1,  7, 23, 59, 59)),
            (datetime(2006,  1,  8, 0, 0, 0), datetime(2006, 1, 14, 23, 59, 59)),
            (datetime(2006,  1, 15, 0, 0, 0), datetime(2006, 1, 21, 23, 59, 59)),
            (datetime(2006,  1, 22, 0, 0, 0), datetime(2006, 1, 28, 23, 59, 59)),
            (datetime(2006,  1, 29, 0, 0, 0), datetime(2006, 2,  4, 23, 59, 59)),
        )
        week_ranges = initial_range.sunday_weeks()
        self._test_ranges(week_ranges, expected_ranges)

        # Test ranges that are smaller than a week within one week
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2006, 1, 2),
                datetime(2006, 1, 4),
            )
        expected_ranges = (
            (datetime(2006,1,1,0,0,0), datetime(2006,1,7,23,59,59)),
        )
        week_ranges = initial_range.sunday_weeks()
        self._test_ranges(week_ranges, expected_ranges)

        # Test ranges that are smaller than a week but span two weeks
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2006, 1, 7),
                datetime(2006, 1, 9),
            )
        expected_ranges =(
            (datetime(2006,1,1,0,0,0), datetime(2006,1,7,23,59,59)),
            (datetime(2006,1,8,0,0,0), datetime(2006,1,14,23,59,59)),
        )
        week_ranges = initial_range.sunday_weeks()
        self._test_ranges(week_ranges, expected_ranges)

    #---------------------------------------------------------------------------
    def test_timeline_range_month_split(self):
        self._test_proper_setup()

        # Test a year long range that includes a leap month.
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2004, 1, 1),
                datetime(2004, 12, 31),
            )
        month_ranges = initial_range.months()
        self._test_ranges(
                month_ranges,
                expected_ranges =(
                    (datetime(2004,  1, 1, 0, 0, 0), datetime(2004,  1, 31, 23, 59, 59)),
                    (datetime(2004,  2, 1, 0, 0, 0), datetime(2004,  2, 29, 23, 59, 59)),
                    (datetime(2004,  3, 1, 0, 0, 0), datetime(2004,  3, 31, 23, 59, 59)),
                    (datetime(2004,  4, 1, 0, 0, 0), datetime(2004,  4, 30, 23, 59, 59)),
                    (datetime(2004,  5, 1, 0, 0, 0), datetime(2004,  5, 31, 23, 59, 59)),
                    (datetime(2004,  6, 1, 0, 0, 0), datetime(2004,  6, 30, 23, 59, 59)),
                    (datetime(2004,  7, 1, 0, 0, 0), datetime(2004,  7, 31, 23, 59, 59)),
                    (datetime(2004,  8, 1, 0, 0, 0), datetime(2004,  8, 31, 23, 59, 59)),
                    (datetime(2004,  9, 1, 0, 0, 0), datetime(2004,  9, 30, 23, 59, 59)),
                    (datetime(2004, 10, 1, 0, 0, 0), datetime(2004, 10, 31, 23, 59, 59)),
                    (datetime(2004, 11, 1, 0, 0, 0), datetime(2004, 11, 30, 23, 59, 59)),
                    (datetime(2004, 12, 1, 0, 0, 0), datetime(2004, 12, 31, 23, 59, 59)),
                )
            )

        # Test ranges that are smaller than a month within one month
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2004, 1, 1),
                datetime(2004, 1, 22),
            )
        month_ranges = initial_range.months()
        self._test_ranges(
                month_ranges,
                expected_ranges =(
                    (datetime(2004,1,1,0,0,0), datetime(2004,1,31,23,59,59)),
                )
            )

        # Test ranges that are smaller than a month that span two months
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2004, 1, 30),
                datetime(2004, 2, 2),
            )
        month_ranges = initial_range.months()
        self._test_ranges(
                month_ranges,
                expected_ranges =(
                    (datetime(2004,1,1,0,0,0), datetime(2004,1,31,23,59,59)),
                    (datetime(2004,2,1,0,0,0), datetime(2004,2,29,23,59,59)),
                )
            )

    #---------------------------------------------------------------------------
    def test_timeline_range_year_split(self):
        self._test_proper_setup()

        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2004, 1, 1),
                datetime(2008, 12, 31),
            )
        year_ranges = initial_range.years()
        self._test_ranges(
                year_ranges,
                expected_ranges = (
                    (datetime(2004,1,1,0,0,0), datetime(2004,12,31,23,59,59)),
                    (datetime(2005,1,1,0,0,0), datetime(2005,12,31,23,59,59)),
                    (datetime(2006,1,1,0,0,0), datetime(2006,12,31,23,59,59)),
                    (datetime(2007,1,1,0,0,0), datetime(2007,12,31,23,59,59)),
                    (datetime(2008,1,1,0,0,0), datetime(2008,12,31,23,59,59)),
                )
            )

        # Test a range that is smaller than a year but is self contained
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2004, 1, 1),
                datetime(2004, 12, 31),
            )
        year_ranges = initial_range.years()
        self._test_ranges(
                year_ranges,
                expected_ranges = (
                    (datetime(2004,1,1,0,0,0), datetime(2004,12,31,23,59,59)),
                )
            )

        # Test a range that is smaller than a year but crosses a boundary
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2004, 12, 31),
                datetime(2005, 1, 1),
            )
        year_ranges = initial_range.years()
        self._test_ranges(
                year_ranges,
                expected_ranges = (
                    (datetime(2004,1,1,0,0,0), datetime(2004,12,31,23,59,59)),
                    (datetime(2005,1,1,0,0,0), datetime(2005,12,31,23,59,59)),
                )
            )

    #---------------------------------------------------------------------------
    def test_timeline_range_decade_split(self):
        self._test_proper_setup()

        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2002, 1, 1),
                datetime(2018, 12, 31),
            )
        decade_ranges = initial_range.decades()
        self._test_ranges(
                decade_ranges,
                expected_ranges = (
                    (datetime(2001,1,1,0,0,0), datetime(2010,12,31,23,59,59)),
                    (datetime(2011,1,1,0,0,0), datetime(2020,12,31,23,59,59)),
                )
            )

        # test a range smaller than one decade that is contained within the
        # decade
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2001, 1, 1),
                datetime(2008, 12, 31),
            )
        decade_ranges = initial_range.decades()
        self._test_ranges(
                decade_ranges,
                expected_ranges = (
                    (datetime(2001,1,1,0,0,0), datetime(2010,12,31,23,59,59)),
                )
            )

        # test some ranges smaller than one decade that spans a decade boundary
        test_cases = (
            # start, end
            (datetime(2010, 1,1), datetime(2012, 12, 31)),
            (datetime(2010, 12,31), datetime(2011, 1, 1)),
        )
        for start_date, end_date in test_cases:
            initial_range = self._create_event_range(self.timeline_event_set.all(), start_date, end_date)
            decade_ranges = initial_range.decades()
            self._test_ranges(
                    decade_ranges,
                    expected_ranges = (
                        (datetime(2001,1,1,0,0,0), datetime(2010,12,31,23,59,59)),
                        (datetime(2011,1,1,0,0,0), datetime(2020,12,31,23,59,59)),
                    )
                )

    #---------------------------------------------------------------------------
    def test_timeline_range_century_split(self):
        self._test_proper_setup()

        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2002, 1, 1),
                datetime(2108, 12, 31),
            )
        century_ranges = initial_range.centuries()
        self._test_ranges(
                century_ranges,
                expected_ranges = (
                    (datetime(2001,1,1,0,0,0), datetime(2100,12,31,23,59,59)),
                    (datetime(2101,1,1,0,0,0), datetime(2200,12,31,23,59,59)),
                )
            )

        # test a range smaller than one century that is contained within the
        # century
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2001, 1, 1),
                datetime(2008, 12, 31),
            )
        century_ranges = initial_range.centuries()
        self._test_ranges(
                century_ranges,
                expected_ranges = (
                    (datetime(2001,1,1,0,0,0), datetime(2100,12,31,23,59,59)),
                )
            )

        # test some ranges smaller than one century that spans a century boundary
        test_cases = (
            # start, end
            (datetime(2100, 1,1), datetime(2102, 12, 31)),
            (datetime(2100, 12,31), datetime(2101, 1, 1)),
        )
        for start_date, end_date in test_cases:
            initial_range = self._create_event_range(self.timeline_event_set.all(), start_date, end_date)
            century_ranges = initial_range.centuries()
            self._test_ranges(
                    century_ranges,
                    expected_ranges = (
                        (datetime(2001,1,1,0,0,0), datetime(2100,12,31,23,59,59)),
                        (datetime(2101,1,1,0,0,0), datetime(2200,12,31,23,59,59)),
                    )
                )

    #---------------------------------------------------------------------------
    def test_timeline_range_millenium_split(self):
        self._test_proper_setup()

        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2002, 1, 1),
                datetime(3008, 12, 31),
            )
        # Check to ensure that the synonym exists
        self.assertEqual(initial_range.millenia, initial_range.milleniums)
        millenium_ranges = initial_range.millenia()
        self._test_ranges(
                millenium_ranges,
                expected_ranges = (
                    (datetime(2001,1,1,0,0,0), datetime(3000,12,31,23,59,59)),
                    (datetime(3001,1,1,0,0,0), datetime(4000,12,31,23,59,59)),
                )
            )

        # test a range smaller than one millenium that is contained within the
        # millenium
        initial_range = self._create_event_range(
                self.timeline_event_set.all(),
                datetime(2001, 1, 1),
                datetime(2008, 12, 31),
            )
        millenium_ranges = initial_range.millenia()
        self._test_ranges(
                millenium_ranges,
                expected_ranges = (
                    (datetime(2001,1,1,0,0,0), datetime(3000,12,31,23,59,59)),
                )
            )

        # test some ranges smaller than one millenium that spans a millenium boundary
        test_cases = (
            # start, end
            (datetime(2998, 1,1), datetime(3002, 12, 31)),
            (datetime(3000, 12,31), datetime(3001, 1, 1)),
        )
        for start_date, end_date in test_cases:
            initial_range = self._create_event_range(self.timeline_event_set.all(), start_date, end_date)
            millenium_ranges = initial_range.millenia()
            self._test_ranges(
                    millenium_ranges,
                    expected_ranges = (
                        (datetime(2001,1,1,0,0,0), datetime(3000,12,31,23,59,59)),
                        (datetime(3001,1,1,0,0,0), datetime(4000,12,31,23,59,59)),
                    )
                )

