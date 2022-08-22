"""
Event related middleware.
"""
from swim.event.models import Event, AllCalendarEvents, Calendar

#-------------------------------------------------------------------------------
def all_calendar_events(request, context, resource, template):
    """
    Update the context to include an 'all_calendar_events' entry.
    """
    context['all_calendar_events'] = AllCalendarEvents()

#-------------------------------------------------------------------------------
def all_calendars(request, context, resource, template):
    """
    Update the context to include an 'all_calendars' entry.
    """
    context['all_calendars'] = Calendar.objects.all()
