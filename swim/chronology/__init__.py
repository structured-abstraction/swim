"""
Facilities for providing date range accessors.


Glossary:

Terms that restrict the timeline to a particular interesting range.
These are the entry points into the system, and one of these must
be the initial term we pass to the timeline.

 * all - the range will extend from the first event to the last event,
   inclusive.
 * starts_after_now - All events that start in the future.
 * ends_after_now - All events in the future, including those that started
   in the past, but end in the future
 * ends_before_now - All events that ended in the past.
 * starts_before_now - All events that started in the past, including those that
   end in the future.
 * now - the date range that includes the smallest range of resolution
   we support.
 * view - the date range specified in the URL [TODO: Implement this]

Once we have initially targetted the general range of the timeline that we
are interested in, we can do one of two things. 1. we can split the range
into smaller chunks or we can ask for a larger range that includes the
current range:

Terms that further refine the target range of dates that we're interested
in.
 * milleniums
 * centuries
 * decades
 * years
 * months
 * weeks, monday_weeks
 * sunday_weeks
 * days
 * hours
 * minutes
 * seconds

Examples (splitting into smaller ranges):

    {# the first year in the entire timeline #}
    {{ timeline.all.years.0 }}

    {# the first month in the ends_before_now range #}
    {{ timeline.ends_before_now.months.0 }}

    {# the first month in the starts_after_now range (Probably this month) #}
    {{ timeline.starts_after_now.months.0 }}

    {# the first month in the range indicated by the current url #}
    {{ timeline.view.months.0 }}

    {# first day of the first month in the entire timeline #}
    {{ timeline.all.months.0.days.0 }}

Examples (choosing larger containing ranges):
    {# Returns the range for the month  containing today. #}
    {{ timeline.now.months.0 }}

    {# Returns the range that covers the today #}
    {{ timeline.now.days.0 }}

    {# Returns the list of months within the year that contains today #}
    {{ timeline.now.year.months.0 }}

    {# Returns the list of days span the millenium that contains today. #}
    {{ timeline.now.millenium.days.0}}

Examples of iterating over these ranges:
    {# iterate over the all of the weeks in the timeline #}
    {% for week in timeline.all.weeks.0 %}
    {% endfor %}

    {# iterate over the starts_after_now months in the timeline. #}
    {% for month in timeline.starts_after_now.months %}
    {% endfor %}


    {# iterate over all of the months in the current iterations month. #}
    {% for month in timeline.starts_after_now.months %}
        {# iterate over all of the weeks in the current iterations month. #}
        {% for week in month.weeks %}
        {% endfor %}
    {% endfor %}

Further, once you have a Calendar range you can restrict the set of events
by resource_type.key:
    {# first event of resource_type 'show' within the timeline. #}
    {{ timeline.all.show.0 }}

    {# first event of resource_type 'event' within the timeline. #}
    {{ timeline.all.event.0 }}

"""
import calendar

from datetime import datetime, timedelta, time

from django.db.models import Q
from django.conf import settings
from django.utils import timezone

#-------------------------------------------------------------------------------
# Constants
# TODO: update these to include milliseconds
MORNING_KWARGS = dict(hour=0, minute=0, second=0)
DAY_LENGTH = timedelta(hours=23, minutes=59, seconds=59)
def get_morning_kwargs():
    return getattr(settings, 'DAY_START_TIME_KWARGS', MORNING_KWARGS)

#-------------------------------------------------------------------------------
# Constants
debug = getattr(settings, 'DEBUG', False)
override = getattr(settings, 'CHRONOLOGY_NOW_OVERRIDE', None)
def get_now():
    if debug and override:
        return override
    if settings.USE_TZ:
        return timezone.localtime(timezone.now())
    return datetime.now()


#-------------------------------------------------------------------------------
class YearBasedRangeCalculator:
    """
    Provides calculations for year based ranges that start on 1.
    """
    def __init__(self, size):
        self.size = size

    def __call__(self, start_date, increment):
        # Find the beginning of the range which is always is a '1' year:
        # Decade Examples: 2001, 2011, 2021, 2031 ...
        # Century Examples: 2001, 2101, 2201, 2301 ...
        # Millenium Examples: 2001, 3001, 4001, 5001 ...
        modulo = start_date.year % self.size
        if modulo == 0:
            # TODO: there is probably some modular arithmetic way of
            #       achieving these special cases, but I don't know it.

            # 0 is a special case cause that means we have to subtract
            # self.size - 1 years.
            #
            # Century Examples:
            # XX00 % 100 = 0, but we want to subtract 99 -> 2000 - 99 = 1901
            # XX10 % 100 = 0, but we want to subtract 99 -> 2100 - 99 = 2001
            # ... etc.
            difference = self.size - 1
        else:
            # All other cases will be 1 too large.
            #
            # Decade Examples:
            # XXX2 % 10 == 2, but we want to subtract 1 -> 2002 - 1 = 2001
            # XXX3 % 10 == 3, but we want to subtract 2 -> 2003 - 2 = 2001
            # ... etc.
            difference = modulo - 1

        beginning_year = start_date.year - difference
        beginning_year += increment * self.size

        range_start_date = start_date.replace(
                year=beginning_year,
                month=1,
                day=1,
                **get_morning_kwargs()
            )
        range_end_date = DAY_LENGTH + range_start_date.replace(
                year=beginning_year+(self.size-1),
                month=12,
                day=31,
                **get_morning_kwargs()
            )
        return range_start_date, range_end_date

#-------------------------------------------------------------------------------
class Chronological:
    #--------------------------------------------------------------------------
    def __init__(self,
            query_set,
            start_datetime_attr='start_timestamp',
            end_datetime_attr='end_timestamp',
            resource_type_attr='resource_type',
            incoming_cached_events=None,
        ):
        self._query_set = query_set

        self._start_datetime_attr = start_datetime_attr
        self._end_datetime_attr = end_datetime_attr
        self._resource_type_attr = resource_type_attr

        self._cached_values = {}

        self._my_cached_events = []
        self._have_generated_cached_events = False
        self._incoming_cached_events = incoming_cached_events


    #---------------------------------------------------------------------------
    def get_cached_events(self):
        if not self._have_generated_cached_events:
            self._have_generated_cached_events = True
            if self._incoming_cached_events is None:
                self._my_cached_events = list(self.get_query_set())
            else:
                self._my_cached_events = self.get_from_cached_events(
                        self._incoming_cached_events,
                        self.start_date,
                        self.end_date
                    )
        return self._my_cached_events

    #---------------------------------------------------------------------------
    def set_cached_events(self, events):
        self._my_cached_events = events
    cached_events = property(get_cached_events, set_cached_events)

    #---------------------------------------------------------------------------
    def duration(self):
        return self.end_date - self.start_date

    #--------------------------------------------------------------------------
    def _get_range(self, cache_name, method):
        cached_value = self._cached_values.get(cache_name, None)
        if cached_value: return cached_value

        try:
            retval = method()
        except IndexError:
            return None

        setattr(self, cache_name, retval)
        return retval

    #--------------------------------------------------------------------------
    def all(self):
        return self._get_range('_all_cache', self._all)

    #--------------------------------------------------------------------------
    def _all(self):
        """
        Returns a Period instance that spans the entire set.
        """
        first_event = self._query_set.exclude(**{
            self._start_datetime_attr + '__isnull': True,
            self._end_datetime_attr + '__isnull': True,
        }).order_by(self._start_datetime_attr)[0]

        last_event = self._query_set.exclude(**{
            self._start_datetime_attr + '__isnull': True,
            self._end_datetime_attr + '__isnull': True,
        }).order_by('-%s' % self._end_datetime_attr)[0]

        return Period(
            self._query_set,
            getattr(first_event, self._start_datetime_attr),
            getattr(last_event, self._end_datetime_attr),
            self._start_datetime_attr,
            self._end_datetime_attr,
            self._resource_type_attr,
        )

    #--------------------------------------------------------------------------
    def now(self):
        """
        Returns a Period instance that spans this exact second.
        """
        now = get_now()
        return Period(
            self._query_set,
            now,
            now,
            self._start_datetime_attr,
            self._end_datetime_attr,
            self._resource_type_attr,
        )

    #--------------------------------------------------------------------------
    def starts_before_now(self):
        return self._get_range('_starts_before_now_cache', self._starts_before_now)

    #--------------------------------------------------------------------------
    def _starts_before_now(self):
        """
        A Period instance that starts this exact second into the future.
        """
        now = get_now()
        first_event = self._query_set.exclude(**{
                '%s__isnull' % self._start_datetime_attr: True
            }).order_by(self._start_datetime_attr)[0]

        return Period(
            self._query_set,
            getattr(first_event, self._start_datetime_attr),
            now,
            self._start_datetime_attr,
            self._end_datetime_attr,
            self._resource_type_attr,
        )

    #--------------------------------------------------------------------------
    def ends_after_now(self):
        return self._get_range('_ends_after_now_cache', self._ends_after_now)

    #--------------------------------------------------------------------------
    def _ends_after_now(self):
        """
        A Period instance that starts this exact second into the future.
        """
        now = get_now()
        last_event = self._query_set.exclude(**{
                "%s__isnull" % self._end_datetime_attr: True
            }).order_by('-%s' % self._end_datetime_attr)[0]

        return Period(
            self._query_set,
            now,
            getattr(last_event, self._end_datetime_attr),
            self._start_datetime_attr,
            self._end_datetime_attr,
            self._resource_type_attr,
        )

    #--------------------------------------------------------------------------
    def starts_after_now(self):
        return self._get_range('_starts_after_now_cache', self._starts_after_now)

    #--------------------------------------------------------------------------
    def _starts_after_now(self):
        """
        Returns a Period instance that spans all of the future events.

        NOTE: this will exclude events that started in the past and end in
        the future.
        """
        now = get_now()
        first_event = self._query_set.filter(**{
                '%s__gt' % self._start_datetime_attr: now,
                '%s__isnull' % self._start_datetime_attr: False
            }).order_by(self._start_datetime_attr)[0]
        last_event = self._query_set.exclude(**{
                "%s__isnull" % self._end_datetime_attr: True,
            }).order_by('-%s' % self._end_datetime_attr)[0]

        return Period(
            self._query_set,
            getattr(first_event, self._start_datetime_attr),
            getattr(last_event, self._end_datetime_attr),
            self._start_datetime_attr,
            self._end_datetime_attr,
            self._resource_type_attr,
        )

    #--------------------------------------------------------------------------
    def ends_before_now(self):
        return self._get_range('_ends_before_now_cache', self._ends_before_now)

    #--------------------------------------------------------------------------
    def _ends_before_now(self):
        """
        Returns a Period instance that spans all of the ends_before_now events.

        NOTE: this will exclude events that start in the ends_before_now and end in the
        future.
        """
        now = get_now()
        first_event = self._query_set.exclude(**{
                '%s__isnull' % self._start_datetime_attr: True
            }).order_by(self._start_datetime_attr)[0]
        last_event = self._query_set.filter(**{
                '%s__isnull' % self._end_datetime_attr: False,
                '%s__lt' % self._end_datetime_attr: now
            }).order_by('-%s' % self._end_datetime_attr)[0]

        return Period(
            self._query_set,
            getattr(first_event, self._start_datetime_attr),
            getattr(last_event, self._end_datetime_attr),
            self._start_datetime_attr,
            self._end_datetime_attr,
            self._resource_type_attr,
        )

    #---------------------------------------------------------------------------
    def get_from_cached_events(self, incoming_events, start_date, end_date):
        """
        Return the list of events that match the passed in date range.
        """
        _my_cached_events = []
        for event in incoming_events:
            event_start = getattr(event, self._start_datetime_attr)
            event_end = getattr(event, self._end_datetime_attr)
            if event_end is None:
                # Deal with events that don't have an end_date by setting it
                # to the start_date
                event_end = event_start

            if event_start > end_date and event_end > end_date:
                continue

            elif event_start < start_date and event_end < start_date:
                continue

            _my_cached_events.append(event)
        return _my_cached_events

    #---------------------------------------------------------------------------
    def events(self):
        return self.cached_events

    #---------------------------------------------------------------------------
    def new_range(self, start_date, end_date):
        # By default the incoming cached events we give the next range is
        # the same ones we received.
        events = self._incoming_cached_events

        # unless they're a smaller range and we have our own cached ones:
        if self.start_date <= start_date and self.end_date >= end_date and self._my_cached_events:
            events = self._my_cached_events
        return Period(
                self._query_set,
                start_date,
                end_date,
                self._start_datetime_attr,
                self._end_datetime_attr,
                self._resource_type_attr,
                events
            )

    #---------------------------------------------------------------------------
    def split_dates_by_delta(self, start_date, end_date, delta):
        range_start_date = start_date
        range_end_date = range_start_date + delta - timedelta(seconds=1)

        ranges = []
        while range_start_date < end_date:
            ranges.append(
                self.new_range(range_start_date, range_end_date)
            )
            range_start_date += delta
            range_end_date += delta
        return ranges

    #---------------------------------------------------------------------------
    def split_dates_by_next_func(self, start_date, end_date, func):
        range_start_date, range_end_date = func(start_date, 0)

        ranges = []
        while range_start_date < end_date:
            ranges.append(
                self.new_range(range_start_date, range_end_date)
            )
            range_start_date, range_end_date = func(range_start_date, 1)
        return ranges

    #---------------------------------------------------------------------------
    def millenia(self):
        """
        Split this range into a list of millenium ranges.
        """
        _get_next_century_range = YearBasedRangeCalculator(1000)
        range_start_date, _ = _get_next_century_range(self.start_date, 0)
        _, end_date = _get_next_century_range(self.end_date, 0)
        return self.split_dates_by_next_func(range_start_date, end_date, _get_next_century_range)
    milleniums = millenia

    #---------------------------------------------------------------------------
    def centuries(self):
        """
        Split this range into a list of century ranges.
        """
        _get_next_century_range = YearBasedRangeCalculator(100)
        range_start_date, _ = _get_next_century_range(self.start_date, 0)
        _, end_date = _get_next_century_range(self.end_date, 0)
        return self.split_dates_by_next_func(range_start_date, end_date, _get_next_century_range)

    #---------------------------------------------------------------------------
    def decades(self):
        """
        Split this range into a list of decade ranges.
        """
        _get_next_decade_range = YearBasedRangeCalculator(10)

        range_start_date, _ = _get_next_decade_range(self.start_date, 0)
        _, end_date = _get_next_decade_range(self.end_date, 0)
        return self.split_dates_by_next_func(range_start_date, end_date, _get_next_decade_range)

    #---------------------------------------------------------------------------
    def years(self):
        """
        Split this range into a list of year ranges.
        """
        def _get_next_year_range(start_date, increment):
            range_start_date = start_date.replace(year=start_date.year+increment, **get_morning_kwargs())
            range_end_date = DAY_LENGTH + range_start_date.replace(month=12, day=31, **get_morning_kwargs())
            return range_start_date, range_end_date

        range_start_date = self.start_date.replace(month=1, day=1, **get_morning_kwargs())
        end_date = DAY_LENGTH + self.end_date.replace(month=12, day=31, **get_morning_kwargs())
        return self.split_dates_by_next_func(range_start_date, end_date, _get_next_year_range)

    #---------------------------------------------------------------------------
    def months(self):
        """
        Split this range into a list of month ranges.
        """
        range_start_date = self.start_date.replace(day=1, **get_morning_kwargs())
        # Get the last day of the month
        last_day = calendar.monthrange(range_start_date.year, range_start_date.month)[1]
        range_end_date = DAY_LENGTH + self.start_date.replace(day=last_day, **get_morning_kwargs())
        end_date = DAY_LENGTH + self.end_date.replace(**get_morning_kwargs())

        ranges = []
        while range_start_date < end_date:
            ranges.append(
                self.new_range(range_start_date, range_end_date)
            )
            next_month = range_end_date + timedelta(days=1)
            range_start_date = next_month.replace(day=1, **get_morning_kwargs())
            last_day = calendar.monthrange(range_start_date.year, range_start_date.month)[1]
            range_end_date = DAY_LENGTH + range_start_date.replace(day=last_day, **get_morning_kwargs())

        return ranges

    #---------------------------------------------------------------------------
    def monday_weeks(self):
        """
        Split this range into a list of week ranages that start on monday.
        """
        delta = timedelta(days=7)
        weekday = self.start_date.weekday()
        range_start_date = self.start_date - timedelta(days=weekday)
        range_start_date = range_start_date.replace(**get_morning_kwargs())
        end_date = DAY_LENGTH + self.end_date.replace(**get_morning_kwargs())
        return self.split_dates_by_delta(range_start_date, end_date, delta)
    weeks = monday_weeks

    #---------------------------------------------------------------------------
    def sunday_weeks(self):
        """
        Split this range into a list of week ranages that start on sunday.
        """
        delta = timedelta(days=7)

        weekday = self.start_date.weekday() + 1
        if weekday == 7:
            weekday = 0
        range_start_date = self.start_date - timedelta(days=weekday)
        range_start_date = range_start_date.replace(**get_morning_kwargs())
        end_date = DAY_LENGTH + self.end_date.replace(**get_morning_kwargs())
        return self.split_dates_by_delta(range_start_date, end_date, delta)

    #---------------------------------------------------------------------------
    def days(self):
        """
        Split this range into a list of day ranges.
        """
        delta = timedelta(days=1)
        range_start_date = self.start_date.replace(**get_morning_kwargs())
        end_date = DAY_LENGTH + self.end_date.replace(**get_morning_kwargs())
        return self.split_dates_by_delta(range_start_date, end_date, delta)

    #---------------------------------------------------------------------------
    def hours(self):
        """
        Split this range into a list of hour ranges.
        """
        delta = timedelta(hours=1)
        range_start_date = self.start_date.replace(minute=0, second=0)
        end_date = self.end_date.replace(minute=59, second=59)
        return self.split_dates_by_delta(range_start_date, end_date, delta)

    #---------------------------------------------------------------------------
    def minutes(self):
        """
        Split this range into a list of minute ranges.
        """
        delta = timedelta(minutes=1)
        range_start_date = self.start_date.replace(second=0)
        end_date = self.end_date.replace(second=59)
        return self.split_dates_by_delta(range_start_date, end_date, delta)

    #---------------------------------------------------------------------------
    def seconds(self):
        """
        Split this range into a list of second ranges.
        """
        delta = timedelta(seconds=1)
        range_start_date = self.start_date
        end_date = self.end_date + delta
        return self.split_dates_by_delta(range_start_date, end_date, delta)

    #---------------------------------------------------------------------------
    def get_base_query_set(self):
        return self._query_set

    #---------------------------------------------------------------------------
    def get_query_set(self):
        if self.cached_qs is None:
            qs = self.get_base_query_set()
            self.cached_qs = qs.exclude(
                    (
                        Q(**{'%s__lt' % self._start_datetime_attr: self.start_date}) &
                        Q(**{'%s__lt' % self._end_datetime_attr: self.start_date})
                    ) | (
                        Q(**{'%s__gt' % self._start_datetime_attr: self.end_date}) &
                        Q(**{'%s__gt' % self._end_datetime_attr: self.end_date})
                    ) | (
                        Q(**{'%s__isnull' % self._start_datetime_attr: True}) &
                        Q(**{'%s__isnull' % self._end_datetime_attr: True})
                    )
                )
        return self.cached_qs

    #---------------------------------------------------------------------------
    def resize_to_events(self):
        try:
            first_event = self.cached_events[0]
            last_event = self.cached_events[-1]
            self.start_date = getattr(first_event, self._start_datetime_attr)
            self.end_date = getattr(last_event, self._end_datetime_attr)

        except IndexError:
            pass

    #---------------------------------------------------------------------------
    def all_types(self):
        """
        Return all events in this range regardless of type.
        """
        return self


#-------------------------------------------------------------------------------
class Period(Chronological):
    """
    Represents a single period within a timeline of events.

    Assumptions:
        start_date and end_date are datetimes not just dates.
    """
    alters_data = False

    #---------------------------------------------------------------------------
    def __init__(self,
        query_set,
        start_date,
        end_date,
        start_datetime_attr='start_timestamp',
        end_datetime_attr='end_timestamp',
        resource_type_attr='resource_type',
        incoming_cached_events=None,
    ):
        self.start_date = start_date
        self.end_date = end_date

        super(Period, self).__init__(
            query_set,
            start_datetime_attr,
            end_datetime_attr,
            resource_type_attr
        )
        self._query_set = query_set
        self._incoming_cached_events = incoming_cached_events
        self.cached_qs = None

    #---------------------------------------------------------------------------
    def __getattr__(self, attname):
        try:
            # Django tries to getattr before it'll try list indexes
            # and because we lazily return resource type restricted date ranges
            # in our getattr, we'll try the list indexing ourself at this point
            # to avoid returning a ResourceTypePeriod for {{ timeline.now.shows.0 }}
            return self[int(attname)]
        except (ValueError, IndexError):
            pass

        rtr = ResourceTypePeriod(
            attname,
            self._query_set,
            self.start_date,
            self.end_date,
            self._start_datetime_attr,
            self._end_datetime_attr,
            self._resource_type_attr,
            self._incoming_cached_events
        )
        # At the moment that we restrict the resource type, also resize
        # the range to be inclusive of all the events.
        rtr.resize_to_events()
        return rtr


    #---------------------------------------------------------------------------
    def all_types(self):
        """
        Return all events in this range regardless of type.
        """
        return self

    #--------------------------------------------------------------------------
    def includes_now(self):
        """
        Returns a boolean indicating if this period includes today or now.
        """
        now = get_now()
        return self.end_date >= now and self.start_date <= now
    is_today = includes_now

    #--------------------------------------------------------------------------
    def is_past(self):
        """
        Returns a boolean indicating if this period is in the past.
        """
        now = get_now()
        if self.end_date < now:
            return True
        return False

    #--------------------------------------------------------------------------
    def is_future(self):
        """
        Returns a boolean indicating if this period is in the future.
        """
        now = get_now()
        if self.start_date > now:
            return True
        return False

    #--------------------------------------------------------------------------
    def is_ongoing(self):
        """
        Returns a boolean indicating if this period is in the future.
        """
        now = get_now()
        if self.end_date >= now and self.start_date <= now:
            return True
        return False
    is_now = is_ongoing


#-------------------------------------------------------------------------------
class ResourceTypePeriod(Period):

    #---------------------------------------------------------------------------
    def __init__(self,
        resourcetype_key,
        query_set,
        start_date,
        end_date,
        start_datetime_attr='start_timestamp',
        end_datetime_attr='end_timestamp',
        resource_type_attr='resource_type',
        incoming_cached_events=None,
    ):
        self.resourcetype_key = resourcetype_key
        super(ResourceTypePeriod, self).__init__(
                query_set,
                start_date,
                end_date,
                start_datetime_attr,
                end_datetime_attr,
                resource_type_attr,
                incoming_cached_events
            )

    #---------------------------------------------------------------------------
    def get_resource_type(self, event):
        cur_obj = event
        for name_part in self._resource_type_attr.split("__"):
            cur_obj = getattr(cur_obj, name_part)
        return cur_obj

    #---------------------------------------------------------------------------
    def get_from_cached_events(self, incoming_events, start_date, end_date):
        """
        Return the list of events that match the passed in date range.
        """
        incoming_events = super(ResourceTypePeriod, self).get_from_cached_events(
                incoming_events, start_date, end_date
            )
        incoming_cached_events = []
        for event in incoming_events:
            if self.get_resource_type(event).key == self.resourcetype_key:
                incoming_cached_events.append(event)
        return incoming_cached_events


    #---------------------------------------------------------------------------
    def new_range(self, start_date, end_date):
        # TODO: it seems this method isn't tested by our tests?!

        # By default the incoming cached events we give the next range is
        # the same ones we received.
        events = self._incoming_cached_events

        return ResourceTypePeriod(
            self.resourcetype_key,
            self._query_set,
            start_date,
            end_date,
            self._start_datetime_attr,
            self._end_datetime_attr,
            self._resource_type_attr,
            events
        )

    #---------------------------------------------------------------------------
    def get_base_query_set(self):
        return self._query_set.filter(**{
                '%s__key' % self._resource_type_attr: self.resourcetype_key
            })

    #---------------------------------------------------------------------------
    def all_types(self):
        """
        Return all events in this range regardless of type.
        """
        return Period(
            self._query_set,
            self.start_date,
            self.end_date,
            self._start_datetime_attr,
            self._end_datetime_attr,
            self._resource_type_attr,
            self._incoming_cached_events
        )

#-------------------------------------------------------------------------------
class Timeline(Chronological):

    #---------------------------------------------------------------------------
    def get_start_date(self):
        if not self._cached_values.get('_start_date', None):
            first_event = self._query_set.exclude(**{
                self._start_datetime_attr + '__isnull': True,
                self._end_datetime_attr + '__isnull': True,
            }).order_by(self._start_datetime_attr)[0]
            self._cached_values['_start_date'] = getattr(first_event, self._start_datetime_attr)
        return self._cached_values['_start_date']
    start_date = property(get_start_date)

    #---------------------------------------------------------------------------
    def get_end_date(self):
        if not self._cached_values.get('_end_date', None):
            last_event = self._query_set.exclude(**{
                self._start_datetime_attr + '__isnull': True,
                self._end_datetime_attr + '__isnull': True,
            }).order_by('-%s' % self._end_datetime_attr)[0]
            self._cached_values['_end_date'] = getattr(last_event, self._end_datetime_attr)
        return self._cached_values['_end_date']
    end_date = property(get_end_date)

    #---------------------------------------------------------------------------
    def get_cached_events(self):
        if not self._cached_values.get('_priv_incoming_cached_events', None):
            self._cached_values['_priv_incoming_cached_events'] = list(self._query_set)
        return self._cached_values['_priv_incoming_cached_events']

    #---------------------------------------------------------------------------
    def set_cached_events(self, events):
        self._my_cached_events = events
    cached_events = property(get_cached_events, set_cached_events)

