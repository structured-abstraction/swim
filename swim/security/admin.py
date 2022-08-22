from django.contrib import admin
from django import forms
from django.contrib.contenttypes.models import ContentType as DjangoContentType

from swim.generic import DisabledWithHidden
from swim.django_admin import (
   register_content_slot_admin,
    ModelAdmin,
    SingleContentSlotInlineAdmin,
    ListContentSlotInlineAdmin,
    UnusedContentSlotInlineAdmin,
)
from swim.security.models import (
        File,
        AccessRestriction,
        SslEncryption,
        SecureFileSlot,
    )

#-------------------------------------------------------------------------------
class SingleSecureFileSlotInlineAdmin(SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = SecureFileSlot
    autocomplete_fields = ('file',)

#-------------------------------------------------------------------------------
class ListSecureFileSlotInlineAdmin(ListContentSlotInlineAdmin):
    model = SecureFileSlot
    autocomplete_fields = ('file',)

#-------------------------------------------------------------------------------
class UnusedSecureFileSlotInlineAdmin(UnusedContentSlotInlineAdmin):
    model = SecureFileSlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.security.File',
    single=SingleSecureFileSlotInlineAdmin,
    list=ListSecureFileSlotInlineAdmin,
    unused=UnusedSecureFileSlotInlineAdmin,
    can_delete=True,
    model=File,
    storage_model=SecureFileSlot,
)

#-------------------------------------------------------------------------------
class SslEncryptionAdmin(ModelAdmin):
    save_on_top = True
    model = SslEncryption
    list_display = ('path', 'force_ssl_connection',)

#-------------------------------------------------------------------------------
class AccessRestrictionAdmin(ModelAdmin):
    save_on_top = True
    model = AccessRestriction
    list_display = ('path', 'only_allow',)

#-------------------------------------------------------------------------------
class FileAdmin(ModelAdmin):
    save_on_top = True
    model = File
    list_display = ('title', 'creationdate', 'modifieddate')

# Content Models
admin.site.register(SslEncryption, SslEncryptionAdmin)
admin.site.register(AccessRestriction, AccessRestrictionAdmin)
admin.site.register(File, FileAdmin)
