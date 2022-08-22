from datetime import datetime, time

from django.db import models
from django.conf import settings
from django.utils import timezone

from swim.chronology.fields import TimeField
from swim.chronology import get_now

#-------------------------------------------------------------------------------
class Event(models.Model):
    """
    Common base class for Period and Instance.
    """

    class Meta:
        abstract = True


#-------------------------------------------------------------------------------
class Period(Event):
    """
    A Period model explicitly stores it's start_datetime and end_datetime, but
    presents it as two separate attributes for admin purposes.
    """

    start_date = models.DateField()
    start_time = TimeField(
            blank=True, null=True,
            help_text = settings.TIME_HELP_STRING
        )

    end_date = models.DateField(blank=True, null=True)
    end_time = TimeField(
            blank=True, null=True,
            help_text = settings.TIME_HELP_STRING
        )

    start_timestamp = models.DateTimeField(blank=True, null=True, editable=False)
    end_timestamp = models.DateTimeField(blank=True, null=True, editable=False)

    #---------------------------------------------------------------------------
    def duration(self):
        return self.end_timestamp - self.start_timestamp

    #--------------------------------------------------------------------------
    def date_string(self):
        date_string = ''
        if self.start_date and self.end_date:
            date_string = '%s-%s' % (
                self.start_timestamp.strftime("%Y/%m/%d %H:%M:%S"),
                self.end_timestamp.strftime("%Y/%m/%d %H:%M:%S"),
            )
        elif self.start_date:
            date_string = '%s' % (
                self.start_timestamp.strftime("%Y/%m/%d %H:%M:%S"),
            )
        elif self.end_date:
            date_string = '%s' % (
                self.end_date.strftime("%Y/%m/%d %H:%M:%S"),
            )
        return date_string

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if self.start_date:
            # Use the start_date if they provided it!
            # Default the start time to 00:00:00
            start_time = self.start_time
            if start_time is None:
                start_time = time(0,0,0)

            timestamp = datetime.combine(self.start_date, start_time)
            if settings.USE_TZ:
                timestamp = timezone.make_aware(timestamp)
            self.start_timestamp = timestamp

        elif self.end_date:
            # Otherwise use the end_date if they provided it.
            # Default the start time to 00:00:00
            start_time = self.start_time
            if start_time is None:
                start_time = time(0,0,0)

            timestamp = datetime.combine(self.end_date, start_time)
            if settings.USE_TZ:
                timestamp = timezone.make_aware(timestamp)
            self.start_timestamp = timestamp


        if self.end_date:
            # Use the end date if they provided it.
            # Default the end time to 23:59:59
            end_time = self.end_time
            if end_time is None:
                end_time = time(23,59,59)

            timestamp = datetime.combine(self.end_date, end_time)
            if settings.USE_TZ:
                timestamp = timezone.make_aware(timestamp)
            self.end_timestamp = timestamp

        elif self.start_date:
            # Use the start_date if they provided it.
            # Default the end time to 23:59:59
            end_time = self.end_time
            if end_time is None:
                end_time = time(23,59,59)

            timestamp = datetime.combine(self.start_date, end_time)
            if settings.USE_TZ:
                timestamp = timezone.make_aware(timestamp)
            self.end_timestamp = timestamp

        super(Period, self).save(*args, **kwargs)

    #--------------------------------------------------------------------------
    def includes_now(self):
        """
        Returns a boolean indicating if this period includes today or now.
        """
        now = get_now().date()
        if self.end_date:
            return self.end_date >= now and self.start_date <= now
        else:
            return self.start_date == now
    is_today = includes_now

    #--------------------------------------------------------------------------
    def is_past(self):
        """
        Returns a boolean indicating if this period is in the past.
        """
        now = get_now()
        if self.end_timestamp < now:
            return True
        return False

    #--------------------------------------------------------------------------
    def is_future(self):
        """
        Returns a boolean indicating if this period is in the future.
        """
        now = get_now()
        if self.start_timestamp > now:
            return True
        return False

    #--------------------------------------------------------------------------
    def is_ongoing(self):
        """
        Returns a boolean indicating if this period is in the future.
        """
        now = get_now()
        if self.end_timestamp >= now and self.start_timestamp <= now:
            return True
        return False
    is_now = is_ongoing


    class Meta:
        abstract = True

#-------------------------------------------------------------------------------
class Instant(Event):
    """
    An instant has only one date associated with it.
    """

    class Meta:
        abstract = True

#-------------------------------------------------------------------------------
class PublishedItemsManager(models.Manager):
    def get_queryset(self):
        return super(PublishedItemsManager, self).get_queryset() \
            .exclude(publish_date__gt=get_now()) \
            .exclude(publish_date__isnull=True) \
            .order_by('-publish_date')

#-------------------------------------------------------------------------------
class PublishedInstant(Instant):
    """
    Blog Post is a dated post.
    """

    publish_date = models.DateField()
    publish_time = models.TimeField()

    publish_timestamp = models.DateTimeField(blank=True, null=True, editable=False)

    published_objects = PublishedItemsManager()

    #--------------------------------------------------------------------------
    def date_string(self) :
        return u"%s %s" % (
                self.publish_date.strftime("%Y/%m/%d"),
                self.publish_time.strftime("%H:%M:%S"),
            )

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if self.publish_date:
            publish_time = self.publish_time or time(0,0,0)

            timestamp = datetime.combine(self.publish_date, publish_time)
            if settings.USE_TZ:
                timestamp = timezone.make_aware(timestamp)
            self.publish_timestamp = timestamp
        else:
            self.publish_timestamp = None

        super(PublishedInstant, self).save(*args, **kwargs)

    class Meta:
        abstract = True

#-------------------------------------------------------------------------------
class AnonymousInstant(Instant):
    """
    A non-named instant in time.

    Provides .date, .time and .timestamp.
    """

    date = models.DateField(blank=True)
    time = models.TimeField(blank=True)

    timestamp = models.DateTimeField(blank=True, null=True, editable=False)

    #--------------------------------------------------------------------------
    def date_string(self) :
        return u"%s %s" % (
                self.date.strftime("%Y/%m/%d"),
                self.time.strftime("%H:%M:%S"),
            )

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if self.date:
            time = self.time or time(0,0,0)

            timestamp = datetime.combine(self.date, time)
            if settings.USE_TZ:
                timestamp = timezone.make_aware(timestamp)
            self.timestamp = timestamp

        super(AnonymousInstant, self).save(*args, **kwargs)

    class Meta:
        abstract = True

