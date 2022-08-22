"""
Events grouped into calendars.

This event system provides two models:
    1. Calendar
    2. Event

Each event is gathered into a calendar.  Calendar extends Timeline
so it provides a domain specific type language which allows one to very
easily target a subset of the events within a particular calendar and iterate
over them.
"""
from django.template.defaultfilters import slugify
from django.db import models
from django.conf import settings

from swim.core import modelfields, string_to_key
from swim.core.models import (
    RequestHandler,
    ResourceType,
)
from swim.core.content import register_content_object
from swim.content.models import LinkResource
from swim.chronology import Timeline
from swim.chronology.models import Period

#-------------------------------------------------------------------------------
class HasTimeline:
    """
    Mixin that provides a published_timeline property
    """

    #--------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(HasTimeline, self).__init__(*args, **kwargs)
        self.timeline = self.get_timeline()

    #--------------------------------------------------------------------------
    def get_timeline(self):
        """
        Returns a published post timeline.
        """
        return Timeline(
            self.event_set.all().order_by('start_timestamp', 'end_timestamp'),
            'start_timestamp',
            'end_timestamp',
            'resource_type',
        )

    #--------------------------------------------------------------------------
    def __getattribute__(self, keyname):
        try:
            return super(HasTimeline, self).__getattribute__(keyname)
        except AttributeError:
            timeline = super(HasTimeline, self).__getattribute__('timeline')
            return getattr(timeline, keyname)


#-------------------------------------------------------------------------------
class Calendar(HasTimeline, LinkResource):
    """
    A calendar has a path, and title and is a resource.
    """
    path = modelfields.Path()
    key = modelfields.Key(max_length=200, editable=True, unique=True)

    #---------------------------------------------------------------------------
    def get_path_reservation_type(self):
        return "tree"

    #---------------------------------------------------------------------------
    def get_request_method(self):
        return "GET"

    #--------------------------------------------------------------------------
    def get_request_handler(self):
        obj, _ = RequestHandler.objects.get_or_create(
                title = 'Calendar PageView',
                function = 'swim.event.views.CalendarView',
            )
        return obj

    #--------------------------------------------------------------------------
    def url(self):
        if self.path.strip('/') == '':
            return '/'
        else:
            return '/%s' % self.path.strip('/')

    #--------------------------------------------------------------------------
    def __str__(self):
        return "%s (%s)" % (
                self.path,
                self.title or "untitled",
            )

    #--------------------------------------------------------------------------
    def get_absolute_url(self):
        return self.url()

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = string_to_key(self.path)
        super(Calendar, self).save(*args, **kwargs)

    #--------------------------------------------------------------------------
    class Meta:
        ordering = ('path',)

register_content_object('calendar', Calendar)


################################################################################
class Event(LinkResource, Period):
    """
    Each member may submit a single application for each call for submission.
    """
    calendar = models.ForeignKey(
        Calendar,
        related_name='event_set',
        on_delete=models.CASCADE,
    )
    name = models.SlugField('Path Atom',
            max_length=200, unique=False, blank=True, null=True,
            help_text='This will automatically be set from the title.'
        )

    #--------------------------------------------------------------------------
    def __repr__(self):
        return "<%s: %s>" % (
                self.resource_type.title,
                str(self)
            )

    #--------------------------------------------------------------------------
    def __str__(self):
        date_string = self.date_string()
        if date_string:
            return '%s: %s' % (
                    self.title,
                    date_string
                )
        else:
            return self.title

    #---------------------------------------------------------------------------
    def get_request_method(self):
        return "GET"

    #--------------------------------------------------------------------------
    def get_request_handler(self):
        obj, _ = RequestHandler.objects.get_or_create(
                title = 'Calendar Event PageView',
                function = 'swim.event.views.EventView',
            )
        return obj

    #--------------------------------------------------------------------------
    def url(self):
        return '%s/%s' % (
                self.calendar.url(),
                self.name,
            )
    #--------------------------------------------------------------------------
    def get_absolute_url(self):
        return self.url()


    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.name and self.start_date:
            self.name = slugify("%s-%s" % (self.title, self.start_date.strftime("%Y-%m-%d"),))
        elif not self.name:
            self.name = slugify("%s-%s" % (self.title, self.id,))

        super(Event, self).save(*args, **kwargs)


    #--------------------------------------------------------------------------
    class Meta:
        unique_together = (
                ('title', 'calendar', 'start_date'),
                ('name', 'calendar',),
            )
        ordering = ('start_timestamp',)
register_content_object('event', Event)


#-------------------------------------------------------------------------------
class AllCalendarEvents(Timeline):

    #--------------------------------------------------------------------------
    def __init__(self):
        # ensure we initialize the ranges mixin properly.
        super(AllCalendarEvents, self).__init__(
            Event.objects.all().order_by('start_timestamp', 'end_timestamp'),
            'start_timestamp',
            'end_timestamp',
            'resource_type',
        )

