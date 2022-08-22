from django.contrib import admin
from django.conf import settings
from django import forms

from swim.membership.models import (
    Member,
)

#-------------------------------------------------------------------------------
class MemberAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('__str__', 'family_name', 'given_name', 'email_address',
        'postal_code',
    )
    search_fields = ('email_address', 'given_name', 'family_name', 'display_name', )
    fields = ('display_name', 'email_address', 'given_name', 'family_name',
        'postal_code',
    )

admin.site.register(Member, MemberAdmin)
