from django import forms
from django.contrib import admin

from swim.core.validators import isValidTemplate
from swim.django_admin import ModelAdmin
from swim.redirect.models import (
        PathRedirect,
    )

#-------------------------------------------------------------------------------
class PathRedirectAdmin(ModelAdmin):
    search_fields = ('path','redirect_type', 'redirect_path')
    save_on_top = True
    list_display = (
        'path',
        'redirect_type',
        'redirect_path',
    )
    list_filter = (
        'redirect_type',
    )


# Design Models
admin.site.register(PathRedirect, PathRedirectAdmin)
