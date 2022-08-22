from swim.content.views import PageView
from swim.event.models import (
    Calendar,
    Event,
)

#-------------------------------------------------------------------------------
class CalendarView(PageView):
    #---------------------------------------------------------------------------
    def get_context(self, request):
        """
        Add in the blog to the context of any blog page.
        """
        return super(CalendarView, self).get_context(request)


    #---------------------------------------------------------------------------
    def match_resource(self, path, request):
        """Override the resource matching to return the Calendar
        """
        return Calendar.objects.get(path=path)

#-------------------------------------------------------------------------------
class EventView(CalendarView):
    #---------------------------------------------------------------------------
    def get_context(self, request):
        """
        Add in the blog to the context of any blog page.
        """
        return super(CalendarView, self).get_context(request)


    #---------------------------------------------------------------------------
    def match_resource(self, path, request):
        """Override the resource matching to return the Calendar
        """
        path, name = self.get_last_path_atom(path)
        calendar = super(EventView, self).match_resource(path, request)
        return Event.objects.get(calendar=calendar, name=name)

