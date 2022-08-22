from django.contrib import admin
from django.conf import settings

from swim.form.models import (
        Form,
        FormField,
        FormFieldType,
        FormFieldChoice,
        FormHandler,
        FormFieldConstructor,
        FormFieldValidator,
        FormFieldArrangement
    )

#-------------------------------------------------------------------------------
class FormFieldTypeAdmin(admin.ModelAdmin):
    save_on_top = True

class FormFieldConstructorAdmin(admin.ModelAdmin):
    save_on_top = True

class FormFieldValidatorAdmin(admin.ModelAdmin):
    save_on_top = True

#-------------------------------------------------------------------------------
class FormFieldChoiceInline(admin.TabularInline):
    model = FormFieldChoice
    extra = 1

class FormFieldAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('form', 'type', 'name',)
    inlines = [
        FormFieldChoiceInline,
    ]

class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 1

class FormFieldArrangementAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('__str__', 'name', )
    inlines = [
        FormFieldInline,
    ]

#-------------------------------------------------------------------------------
class FormAdmin(admin.ModelAdmin):
    save_on_top = True

#-------------------------------------------------------------------------------
class FormHandlerAdmin(admin.ModelAdmin):
    save_on_top = True

# Register the FormAdmin
admin.site.register(FormFieldArrangement, FormFieldArrangementAdmin)
admin.site.register(FormField, FormFieldAdmin)
admin.site.register(FormFieldType, FormFieldTypeAdmin)
admin.site.register(FormFieldConstructor, FormFieldConstructorAdmin)
admin.site.register(FormFieldValidator, FormFieldValidatorAdmin)
admin.site.register(FormHandler, FormHandlerAdmin)
admin.site.register(Form, FormAdmin)
