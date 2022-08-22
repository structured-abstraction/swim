from django import forms
from django.contrib import admin

from swim.core.validators import isValidTemplate
from swim.django_admin import ModelAdmin
from swim.design.models import (
        Template,
        CSS,
        JavaScript,
        Image as DesignImage,
    )

class TemplateAdmin(ModelAdmin):
    search_fields = ('path','body')
    save_on_top = True
    list_display = (
        'path',
        'swim_content_type',
        'http_content_type',
        'creationdate',
        'modifieddate'
    )
    fieldsets = (
        (None, {
            'fields': ('path', 'body',)
        }),
        ('Domains', {
            'fields' : ('domains',)
        }),
        ('Advanced', {
            'classes': ('collapse', ),
            'fields' : ('http_content_type', 'swim_content_type')
        }),
    )
    list_filter = (
        'http_content_type',
        'swim_content_type',
        'creationdate',
        'modifieddate'
    )

#-------------------------------------------------------------------------------
class CSSAdmin(ModelAdmin):
    list_display = ('path', 'creationdate', 'modifieddate')
    save_on_top = True

#-------------------------------------------------------------------------------
class JavaScriptAdmin(ModelAdmin):
    list_display = ('path', 'creationdate', 'modifieddate')
    save_on_top = True

#-------------------------------------------------------------------------------
class DesignImageAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('filename', 'url', 'creationdate', 'modifieddate')


# Design Models
admin.site.register(Template, TemplateAdmin)
admin.site.register(CSS, CSSAdmin)
admin.site.register(JavaScript, JavaScriptAdmin)
admin.site.register(DesignImage, DesignImageAdmin)
