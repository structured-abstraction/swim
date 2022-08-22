from datetime import datetime

from django.contrib import admin

from swim.django_admin import ResourceModelAdmin
from swim.syndication.models import RSSFeed


#-------------------------------------------------------------------------------
class RSSFeedAdmin(ResourceModelAdmin):
    save_on_top = True
    list_display = ('path', 'blog',)


admin.site.register(RSSFeed, RSSFeedAdmin)

