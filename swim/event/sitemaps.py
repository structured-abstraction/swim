from swim.event.models import Calendar, Event
from swim.seo.sitemaps import SwimSitemap, sitemap_dict

#-------------------------------------------------------------------------------
class CalendarSitemap(SwimSitemap):
    model = Calendar
sitemap_dict['calendars'] = CalendarSitemap

#-------------------------------------------------------------------------------
class EventSitemap(SwimSitemap):
    model = Event
sitemap_dict['events'] = EventSitemap
