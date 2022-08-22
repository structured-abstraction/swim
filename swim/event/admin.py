from datetime import datetime

from django.contrib import admin
from django import forms

from swim.django_admin import ResourceModelAdmin, SearchField
from swim.core.models import ResourceType
from swim.event.models import Event, Calendar
from swim.content.models import Page
from swim.seo.admin import SEO_FIELDSET


#-------------------------------------------------------------------------------
class EventAdmin(ResourceModelAdmin):
    save_on_top = True
    list_display = ('title', 'type', 'calendar', 'url',
            'start_date', 'end_date', )
    list_display_links = ('title',)
    list_filter = ('calendar',)
    date_hierarchy = 'start_date'

    fieldsets = (
        (None, {
            'fields': ('resource_type', 'calendar', 'title',
                'start_date', 'start_time',
                'end_date', 'end_time'),
        }),
        ('Advanced Path Options', {
            'classes': ('collapse',),
            'fields': ('name', )
        }),
        SEO_FIELDSET,
    )

    search_fields = (
            'title',
            'start_date',
            'end_date',
            'resource_type__title',
            'calendar__title',
            'calendar__path',
        )

    type = SearchField('resource_type', 'Type', 'resource_type')


    inlines = []

admin.site.register(Event, EventAdmin)

#-------------------------------------------------------------------------------
class CalendarAdmin(ResourceModelAdmin):
    save_on_top = True
    list_display = ('__str__', 'resource_type')

    fieldsets = (
        (None, {
            'fields': ('resource_type', 'path', 'title',)
        }),
        ('Advanced Path Options', {
            'classes': ('collapse',),
            'fields': ('key', )
        }),
        SEO_FIELDSET,
    )


    inlines = []

admin.site.register(Calendar, CalendarAdmin)
