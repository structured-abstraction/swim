"""
The SWIM administration interface provided by django.
"""
from datetime import datetime
import operator
from functools import partial, update_wrapper
import json

from django.contrib import admin
from django.contrib.admin import widgets
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.admin.options import flatten_fieldsets
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.db import models
from django import forms
from django.forms import ALL_FIELDS
from django.forms.widgets import HiddenInput
from django.forms.models import modelform_defines_fields
from ckeditor_uploader.widgets import CKEditorUploadingWidget

from swim.generic import (
    ListResourceFormSet,
    SingleResourceFormSet,
    FormSetFactory,
    FormFieldFromDBFieldFactory,
    DisabledWithHidden,
)

from swim.django_admin import views
from swim.design.models import ResourceTypeTemplateMapping
from swim.core.models import (
        ArrangementType,
        ArrangementTypeMapping,
        ContentSchema,
        ContentSchemaMember,
        ContentType as SwimContentType,
        DefaultResourceTypeMapping,
        EnumType,
        EnumTypeChoice,
        HasResourceType,
        RequestHandler,
        ResourceType,
        ResourceTypeMiddleware,
        ResourceTypeMiddlewareMapping,
        ResourceTypeResponseProcessor,
        ResourceTypeResponseProcessorMapping,
        ResourceTypeSwimContentTypeMapping,
    )
from functools import reduce

#-------------------------------------------------------------------------------
RESOURCE_JS = [
    settings.DOJO_JS,
    settings.EDITAREA_JS,
    settings.RESOURCE_TEXTAREA_JS,
]

#-------------------------------------------------------------------------------
SWIM_ADMIN_CSS = {
    "all": [
        '/static/swim/css/swim.css',
    ],
}

#-------------------------------------------------------------------------------
TEXTAREA_JS = RESOURCE_JS

#-------------------------------------------------------------------------------
def get_current_type(obj, type_field_name):
    """
    Retreive the _current_ resource type, not the type that's ABOUT to be set.

    Using this helps solves #787 in Mantis.
    """
    if not obj:
        return None
    else:
        try:
            return getattr(obj.__class__.objects.get(id=obj.id), type_field_name)
        except obj.__class__.DoesNotExist:
            return getattr(obj, type_field_name)

#-------------------------------------------------------------------------------
class SearchField:
    """
    Attach to a ModelAdmin to turn an attribute into a clickable search link.

    Example:
        class EventAdmin(ModelAdmin):
            list_display= ('type',)
            type = SearchField('type', short_description='Type')
    """

    def __init__(self, attribute, short_description = None, admin_order_field=None):
        self.attribute = attribute
        self.short_description = short_description
        self.admin_order_field = admin_order_field

    def __call__(self, obj):
        value = getattr(obj, self.attribute)
        return mark_safe(f'<a href="?q={value}">{value}</a>')

#-------------------------------------------------------------------------------
class ChangeWidgetMixin:
    """
    Base class which provides a simple API for providing alternative widgets.
    """
    widget_overrides = {}

    #---------------------------------------------------------------------------
    def formfield_for_dbfield(self, db_field, **kwargs):
        ff = super(ChangeWidgetMixin, self).formfield_for_dbfield(
                db_field, **kwargs)
        if db_field.name in self.widget_overrides:
            widget_info = self.widget_overrides[db_field.name]
            attrs = kwargs.get('attrs', {})
            attrs.update(widget_info.get('attrs', {}))
            ff.widget = widget_info['widget'](attrs=attrs)
        return ff

#-------------------------------------------------------------------------------
class TextInputMixin(ChangeWidgetMixin):
    """
    Uses a default text input area for the _body attributes.
    """
    widget_overrides = {
        'body': {
            'attrs': {
                'size': 255,
            },
            'widget': widgets.AdminTextInputWidget,
        }
    }

#-------------------------------------------------------------------------------
class TextAreaMixin(ChangeWidgetMixin):
    """
    Uses a text area input for the _body attributes.
    """
    widget_overrides = {
        'body': {
            'attrs': {
                'class': 'swimTextArea vLargeTextField',
            },
            'widget': widgets.AdminTextareaWidget,
        }
    }

#-------------------------------------------------------------------------------
class TinyMCEMixin(ChangeWidgetMixin):
    """
    Uses tinymce for the _body attributes.
    """
    widget_overrides = {
        'body': {
            'attrs': {
                'class': 'swimTinyMCE',
            },
            'widget': widgets.AdminTextareaWidget,
        }
    }

#-------------------------------------------------------------------------------
class CKEditorMixin(ChangeWidgetMixin):
    """
    Uses ckeditor for the _body attributes.
    """
    widget_overrides = {
        'body': {
            'widget': CKEditorUploadingWidget,
        },
    }

#-------------------------------------------------------------------------------
class EditAreaMixin(ChangeWidgetMixin):
    """
    Uses Edit Area for the _body attributes.
    """
    widget_overrides = {
        'body': {
            'attrs': {
                'class': 'swimEditArea',
            },
            'widget': widgets.AdminTextareaWidget,
        }
    }

#-------------------------------------------------------------------------------
class BaseContentSlotInlineAdmin(GenericTabularInline):
    def __init__(self, key, title, parent_model, admin_site, interface=None):
        self.key = key
        self.interface = interface
        self.title = title
        self.ct_field = "django_content_type"
        super(BaseContentSlotInlineAdmin, self).__init__(parent_model, admin_site)

    # TODO: Write a custom template?
    # template = '????'

    def get_verbose_name(self):
        return self.title
    verbose_name = verbose_name_plural = property(get_verbose_name)

    #---------------------------------------------------------------------------
    def get_formfield_for_dbfield(self, request, obj=None):
        """
        By default, create the form fields in the same way.
        """
        return self.formfield_for_dbfield

    #---------------------------------------------------------------------------
    def get_formset(self, request, obj=None, **kwargs):
        """
        TODO: SWIM1_11 - test this!
        This is overridden from django/contrib/contenttypes/admin.py line 92ish
        It should, more or less stay up to date with that but update a few things.

        The primary thing it does is return our own FormsetFactory and include
        the interface attribute (right at the end of the function). Otherwise it's the same
        """
        if 'fields' in kwargs:
            fields = kwargs.pop('fields')
        else:
            fields = flatten_fieldsets(self.get_fieldsets(request, obj))
        exclude = [*(self.exclude or []), *self.get_readonly_fields(request, obj)]
        if self.exclude is None and hasattr(self.form, '_meta') and self.form._meta.exclude:
            # Take the custom ModelForm's Meta.exclude into account only if the
            # GenericInlineModelAdmin doesn't define its own.
            exclude.extend(self.form._meta.exclude)
        exclude = exclude or None
        can_delete = self.can_delete and self.has_delete_permission(request, obj)
        defaults = {
            'ct_field': self.ct_field,
            'fk_field': self.ct_fk_field,
            'form': self.form,
            'formfield_callback': partial(self.formfield_for_dbfield, request=request),
            'formset': self.formset,
            'extra': self.get_extra(request, obj),
            'can_delete': can_delete,
            'can_order': False,
            'fields': fields,
            'min_num': self.get_min_num(request, obj),
            'max_num': self.get_max_num(request, obj),
            'exclude': exclude,
            **kwargs,
        }

        if defaults['fields'] is None and not modelform_defines_fields(defaults['form']):
            defaults['fields'] = ALL_FIELDS

        # NOTE: SWIMOVERRIDE
        # SWIM: differences start here, normally django just returns the value of this
        #       call, but we further wrap it in a factory.
        formset = generic_inlineformset_factory(self.model, **defaults)
        if self.interface:
            return FormSetFactory(formset, interface=self.interface, key=None, title=None)
        else:
            return FormSetFactory(formset, interface=None, key=self.key, title=self.title)



#-------------------------------------------------------------------------------
class ContentSlotInlineAdmin(BaseContentSlotInlineAdmin):
    template = 'admin/swim_tabular.html'

#-------------------------------------------------------------------------------
class SingleContentSlotInlineAdmin(ContentSlotInlineAdmin):
    template = "admin/swim_single_inline_stacked.html"
    max_num = 1

    # Exclude order and key by default.
    exclude = ('order', 'key',)

    formset = SingleResourceFormSet

    #---------------------------------------------------------------------------
    def get_queryset_by_key(cls, obj, key):
        if obj is None:
            return cls.model._default_manager.none()
        return cls.model._default_manager.filter(**{
            'django_content_type': DjangoContentType.objects.get_for_model(obj),
            'object_id': obj.pk,
            'key':key,
        })
    get_queryset_by_key = classmethod(get_queryset_by_key)

#-------------------------------------------------------------------------------
class UnusedContentSlotInlineAdmin(SingleContentSlotInlineAdmin):
    """
    Used for all of those resources which do not fit in the resource type.
    """
    # Don't allow them to add extra
    max_num = 1

    template = 'admin/swim_tabular_unused.html'

    # Exclude order and key by default.
    exclude = ('order', )

    formset = SingleResourceFormSet

    #---------------------------------------------------------------------------
    def get_queryset_for_obj(cls, obj):
        if obj is None:
            return cls.model._default_manager.none()
        return cls.model._default_manager.filter(**{
            'django_content_type': DjangoContentType.objects.get_for_model(obj),
            'object_id': obj.pk,
        })
    get_queryset_for_obj = classmethod(get_queryset_for_obj)

    #---------------------------------------------------------------------------
    def set_obj(self, obj):
        self.obj = obj

    #---------------------------------------------------------------------------
    def set_swim_content_type(self, swim_content_type):
        self.swim_content_type = swim_content_type

    #---------------------------------------------------------------------------
    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Override Django's specific rendering for only the entity_type field.
        """
        formfield = super(UnusedContentSlotInlineAdmin, self).formfield_for_dbfield(
                db_field, **kwargs)
        if formfield and db_field.attname == 'key':
            choices = [
                (self.key, self.key),
            ]
            # If we're editing an object show the inlines!
            entity_type = get_current_type(self.obj, self.obj.type_field_name)

            # First step - add in the interfaces based on the resource entity_type
            for interface in ContentSchemaMember.objects.filter(
                    content_schema = entity_type.content_schema
                ).order_by('order'):
                if interface.swim_content_type == self.swim_content_type:
                    choices.append((interface.key,interface.title))

            # Set the choices so they have an option to push this content
            # back into a usable spot.
            formfield.widget = forms.Select(
                attrs=formfield.widget.attrs,
                choices = choices,
            )
        return formfield

#-------------------------------------------------------------------------------
class ListContentSlotInlineAdmin(ContentSlotInlineAdmin):
    extra = 0
    # Exclude key by default.
    exclude = ('key',)

    formset = ListResourceFormSet


# In order to have this definition at the module level, we use the unique title
# that the swim_content_type records will have, rather than their id's or
# references to the model instance.  (This avoids db errors, when this module
# is imported before the database is created).
INLINE_ADMIN_LOOKUP = {}

def register_content_slot_admin(
        type_key, single, list, unused, can_delete, model, storage_model
    ):
    global INLINE_ADMIN_LOOKUP
    INLINE_ADMIN_LOOKUP[type_key] = {
            'single': single,
            'list': list,
            'unused': unused,
            'can_delete': can_delete,
            'model': model,
            'storage_model': storage_model,
        }


#-------------------------------------------------------------------------------
def get_unused_admin_types():
    content_slots_with_unused_form = []
    for key, value in INLINE_ADMIN_LOOKUP.items():
        if value.get('unused'):
            content_slots_with_unused_form.append(key)
    for at in ArrangementType.objects.select_related('_swim_content_type').all():
        content_slots_with_unused_form.append(at.swim_content_type().title)
    return content_slots_with_unused_form


INLINE_ADMIN_LOOKUP_GENERATOR = []

#-------------------------------------------------------------------------------
def register_content_slot_admin_generator(generator):
    global INLINE_ADMIN_LOOKUP_GENERATOR
    INLINE_ADMIN_LOOKUP_GENERATOR.append(generator)


#-------------------------------------------------------------------------------
def get_inline_admin_lookup(key):
    if key in INLINE_ADMIN_LOOKUP:
        return INLINE_ADMIN_LOOKUP[key]

    for generator in INLINE_ADMIN_LOOKUP_GENERATOR:
        val = generator(key)
        if val:
            return val
    return None

#-------------------------------------------------------------------------------
class ModelAdmin(admin.ModelAdmin):
    """
    Override some of django's stupidity.
    """

    def response_add(self, request, obj):
        """
        Override the HttpResponse for the add-view stage.

        In this case we override it to change the JS call that's made.
        """

        # In django's world, _continue takes precedence, so if it's there.
        # just continue on normally. Also, if we don't have a popup, continue
        # normally, otherwise, return the popup closer.
        if "_continue" in request.POST or "_popup" not in request.POST:
            return super(ModelAdmin, self).response_add(request, obj)

        return self.close_popup(request, obj)

    def response_change(self, request, obj):
        """
        Override the HttpResponse for the change_view stage.

        Overriding this method allows us to use the popup window editing in
        django's admin for the change stage as well as the add stage.
        When using the popup window we want the window to close on a proper
        save. However, django usually only returns the appropriate
        "close-window" response during the add stage.
        """

        # In django's world, _continue takes precedence, so if it's there.
        # just continue on normally. Also, if we don't have a popup, continue
        # normally, otherwise, return the popup closer.
        if "_continue" in request.POST or "_popup" not in request.POST:
            return super(ModelAdmin, self).response_change(request, obj)

        return self.close_popup(request, obj)


    def close_popup(self, request, obj):
        opts = obj._meta
        pk_value = obj._get_pk_val()

        msg = _('The %(name)s "%(obj)s" was changed successfully.') % {
                'name': str(opts.verbose_name), 'obj': str(obj)}
        self.message_user(request, msg + ' ' + _("You may edit it again below."))
        return HttpResponse('''
            <script type="text/javascript">
                opener.swim_dismissAddAnotherPopup(window, "%s", "%s");
                opener.dismissAddAnotherPopup(window, "%s", "%s");
            </script>''' % \
                # escape() calls force_unicode.
                (
                    escape(pk_value), escape(obj),
                    escape(pk_value), escape(obj))
                )

    class Media:
        js = list(TEXTAREA_JS) + [
            "/static/swim/js/backend-admin.js",
        ]

        css = SWIM_ADMIN_CSS

#-------------------------------------------------------------------------------
class EntityModelAdmin(ModelAdmin):
    """
    Contains the common implementations of the EntityModelAdmin and
    ArrangmentAdmin classes.
    """
    type_model = None

    #---------------------------------------------------------------------------
    def type_queryset(self, current_type_id = None):
        """
        By default all types are game.
        """
        return self.type_model.objects.all()

    #---------------------------------------------------------------------------
    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Override Django's specific rendering for only the type field.
        """
        # Override the type field.
        # For ForeignKey or ManyToManyFields, use a special widget.
        if isinstance(db_field, models.ForeignKey) and \
                db_field.name == self.model.type_field_name:
            kwargs['required'] = True
            kwargs['label'] = 'Type'
            kwargs['queryset'] = self.type_queryset()

        return super(EntityModelAdmin, self).formfield_for_dbfield(
                db_field, **kwargs)


    #--------------------------------:-------------------------------------------
    def get_form(self, request, obj=None, **kwargs):
        """
        Dynamically configure the form for the add and change stage.

        Overriding this method allows us to exclude the resource type at the
        change stage.
        """

        # If we were asked for a just a particular interface element, ignore
        # all else:
        if obj and request.GET.get('_popup') and request.GET.get('_frontend'):
            opts = obj._meta
            exclude = kwargs.get('exclude', list())
            for f in opts.fields + opts.many_to_many:
                exclude.append(f.name)

            kwargs['exclude'] = exclude

        FormClass = super(EntityModelAdmin, self).get_form(request, obj, **kwargs)

        resource_type_field = FormClass.declared_fields.get(self.model.type_field_name, None)
        if not resource_type_field:
            resource_type_field = FormClass.base_fields.get(self.model.type_field_name, None)

        # In the case that we're editing, let's disable the admin interface for the type.
        entity_type = None
        force_entity_type = False
        resource_types = ResourceTypeSwimContentTypeMapping.objects.filter(
            swim_content_type=self.model.swim_content_type()
        )
        arrangement_types = ArrangementTypeMapping.objects.filter(
            swim_content_type=self.model.swim_content_type()
        )

        # Determing the current Entity Type.
        if obj:
            entity_type = get_current_type(obj, self.model.type_field_name)

        elif request.GET.get('type'):
            entity_type = self.type_model.objects.get(id=request.GET.get('type'))
            force_entity_type = True

        else:
            if self.type_model == ResourceType:
                if resource_types.count() == 1:
                    entity_type = resource_types[0].resource_type

            elif self.type_model == ArrangementType:
                if arrangement_types.count() == 1:
                    entity_type = arrangement_types[0].arrangement_type

        # If there is only one option for the Entity Type, hide the field.
        if self.type_model == ResourceType:
            if resource_types.count() == 1:
                force_entity_type = True

        elif self.type_model == ArrangementType:
            if arrangement_types.count() == 1:
                force_entity_type = True

        # Regardless of whether we're editing or adding a new one, if they
        # asked for a specific entity type, of there is only one, don't show them
        # or let them change type here.
        if force_entity_type:
            # We're assuming that we're using a relatedfield wrapper
            resource_type_field.widget = DisabledWithHidden(resource_type_field.widget.widget)
            resource_type_field.initial = entity_type.id

        if entity_type:
            # Restrict the queryset, but also ensure that we include the selected resource
            # entity_type in the options even if it's not normally allowed
            resource_type_field.queryset = self.type_queryset(current_type_id=entity_type.id)
            resource_type_field.widget.widget.choices = resource_type_field.choices

        return FormClass

    #---------------------------------------------------------------------------
    def get_inline_instances(self, request, obj=None):
        """
        Dynamically create the set of inline instances based on the schema.

        Overriding this method allows us to dynamically create them based
        on the related resource entity_type interface objects that describe what
        the administration interface for this resource should look like.
        During the add stage we can display no inline administration
        interfaces.  During the change stage we show _only_ those which
        are relevant for that entity_type of interface.
        """

        # These mappings are here, because we don't want them to happen until well
        # after the the database has been created.

        inline_instances = []
        entity_type = None
        allow_initial_formsets = True
        if request.GET.get('no_initial_formsets'):
            allow_initial_formsets = False

        if obj:
            # If we're editing an object show the inlines!
            entity_type = get_current_type(obj, self.model.type_field_name)

        elif request.GET.get('type'):
            # OR, if we already know the entity_type of the resource
            # show the inlines.
            entity_type = self.type_model.objects.get(id=request.GET.get('type'))

        elif allow_initial_formsets:
            if self.type_model == ResourceType:
                resource_types = ResourceTypeSwimContentTypeMapping.objects.filter(
                    swim_content_type=self.model.swim_content_type()
                )
                if len(resource_types) == 1:
                    entity_type = resource_types[0].resource_type

            elif self.type_model == ArrangementType:
                resource_types = ArrangementTypeMapping.objects.filter(
                    swim_content_type=self.model.swim_content_type()
                )
                if len(resource_types) == 1:
                    entity_type = resource_types[0].arrangement_type

            else: # type_model == ArrangementType:
                pass # TODO: we should actually handle type_model == ArrangementType:


        if entity_type:
            used_keys = []
            desired_popup_key = None
            if obj and request.GET.get('_popup') and request.GET.get('_frontend'):
                desired_popup_key = request.GET.get('_frontend', None)

            # First step - add in the interfaces based on the resource type
            for interface in ContentSchemaMember.objects.filter(
                    content_schema = entity_type.content_schema
                ).order_by('order'):

                # Record that this key combination was used so that
                # we don't use it again.
                admin_config = get_inline_admin_lookup(interface.swim_content_type.title)
                used_keys.append((admin_config['storage_model'], interface.key))

                # If we were asked for a just a particular interface element, ignore
                # all others
                if desired_popup_key is not None and interface.key != desired_popup_key:
                    continue

                if interface.cardinality == 'single':
                    inline_class = admin_config['single']
                    can_delete = admin_config['can_delete']
                    inline_instance = inline_class(
                            interface.key,
                            interface.title,
                            self.model,
                            self.admin_site,
                            interface=interface
                        )

                    # Here, we update the maximum number of form elements that we'll have for
                    # this cardinality.  We want to always have at least one because we'll need one
                    # to add copy when there is none, but we'll also want to ensure that we
                    # show all of the potential copy that is available here.
                    inline_instance.max_num = max(
                            1,
                            inline_instance.get_queryset_by_key(obj, interface.key).count()
                        )
                    inline_instances.append(inline_instance)

                elif interface.cardinality == 'list':
                    inline_class = admin_config['list']
                    inline_instance = inline_class(
                            interface.key,
                            interface.title,
                            self.model,
                            self.admin_site,
                            interface=interface
                        )
                    inline_instances.append(inline_instance)

            # Second step - add in all of the interfaces for the related content that's NOT
            # based on the resource type.
            # This allows us to show the user all the old content.

            # We only do this step if we're not in a popup
            if desired_popup_key is None:
                unused_admin_types = get_unused_admin_types()
                for swim_content_type_title in unused_admin_types:
                    admin_config = get_inline_admin_lookup(swim_content_type_title)
                    inline_class = admin_config['unused']
                    keys = [resourceobj.key for resourceobj in inline_class.get_queryset_for_obj(obj)]
                    keys = set(keys)
                    for key in keys:
                        # If we've already used this combo above don't do it again.
                        if (admin_config['storage_model'], key) in used_keys:
                            continue
                        used_keys.append((admin_config['storage_model'], key))

                        title = "Unused %s" % inline_class.model._meta.verbose_name_plural
                        inline_instance = inline_class(
                                key,
                                title,
                                self.model,
                                self.admin_site,
                            )
                        inline_instance.set_obj(obj)
                        inline_instance.set_swim_content_type(
                                admin_config['model'].swim_content_type()
                            )
                        inline_instance.max_num = inline_instance.get_queryset_by_key(obj, key).count()
                        inline_instances.append(inline_instance)

        inline_instances.extend(super(ModelAdmin, self).get_inline_instances(request, obj))
        return inline_instances

#-------------------------------------------------------------------------------
class ResourceModelAdmin(EntityModelAdmin):
    """
    Admin class which customizes the admin for objects with a resource type.
    """

    type_model = ResourceType
    resource_type = forms.ModelChoiceField(queryset=type_model.objects.all())

    #---------------------------------------------------------------------------
    def type_queryset(self, current_type_id = None):
        """
        Only a subset of resource types are mapped to being selectable.
        """
        if current_type_id is None:
            return self.type_model.objects.filter(
                    adminable_set__swim_content_type=self.model.swim_content_type()
                )
        else:
            return self.type_model.objects.filter(
                    models.Q(adminable_set__swim_content_type=self.model.swim_content_type()) |
                    models.Q(id = current_type_id)
                )

#-------------------------------------------------------------------------------
class ArrangementModelAdmin(EntityModelAdmin):
    """
    Admin class which customizes the admin for objects with an arrangement type.
    """

    type_model = ArrangementType
    resource_type = forms.ModelChoiceField(queryset=type_model.objects.all())

    #---------------------------------------------------------------------------
    def type_queryset(self, current_type_id = None):
        """
        Only a subset of resource types are mapped to being selectable.
        """
        if current_type_id is None:
            return self.type_model.objects.filter(
                    adminable_set__swim_content_type=self.model.swim_content_type()
                )
        else:
            return self.type_model.objects.filter(
                    models.Q(adminable_set__swim_content_type=self.model.swim_content_type()) |
                    models.Q(id = current_type_id)
                )

#-------------------------------------------------------------------------------
class ResourceTypeMiddlewareMappingAdmin(ModelAdmin):
    save_on_top = True
    list_display = (
        'resource_type',
        'function'
    )
admin.site.register(ResourceTypeMiddlewareMapping, ResourceTypeMiddlewareMappingAdmin)

#-------------------------------------------------------------------------------
class ResourceTypeMiddlewareAdmin(ModelAdmin):
    save_on_top = True
admin.site.register(ResourceTypeMiddleware, ResourceTypeMiddlewareAdmin)

#-------------------------------------------------------------------------------
class ResourceTypeResponseProcessorMappingAdmin(ModelAdmin):
    model = ResourceTypeResponseProcessorMapping
    save_on_top = True
    list_display = (
        'resource_type',
        'function'
    )
admin.site.register(ResourceTypeResponseProcessorMapping, ResourceTypeResponseProcessorMappingAdmin)

#-------------------------------------------------------------------------------
class ResourceTypeResponseProcessorAdmin(ModelAdmin):
    model = ResourceTypeResponseProcessor
    save_on_top = True
admin.site.register(ResourceTypeResponseProcessor, ResourceTypeResponseProcessorAdmin)

#-------------------------------------------------------------------------------
class ResourceTypeTemplateInline(admin.TabularInline):
    template = "admin/swim_tabular.html"
    model = ResourceTypeTemplateMapping
    extra = 0

CONTENT_TYPE_GENERATING_MODELS = []
def register_model_generates_csm_types(model):
    global CONTENT_TYPE_GENERATING_MODELS
    CONTENT_TYPE_GENERATING_MODELS.append(model)

register_model_generates_csm_types(ArrangementType)

#-------------------------------------------------------------------------------
class ContentSchemaMemberInline(admin.TabularInline):
    template = "admin/swim_tabular.html"
    model = ContentSchemaMember
    extra = 0

    #---------------------------------------------------------------------------
    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Override Django's specific rendering for only the resource_type field.
        """
        # Ensure that only the set of content type objects for which we have
        # interfaces available for will be selectable.
        if isinstance(db_field, models.ForeignKey) and \
                db_field.name == 'swim_content_type':

            # First make sure we've installed all of the swim_content_types
            # that we need.
            titles = []
            for admin_config in INLINE_ADMIN_LOOKUP.values():
                model = admin_config['model']
                ct = model.swim_content_type()
                titles.append(ct.title)

            # Also install all of the swim_content_type for each
            # arrangement types.
            for model in CONTENT_TYPE_GENERATING_MODELS:
                for instance in model.objects \
                        .select_related('_swim_content_type').all():
                    titles.append(instance.swim_content_type().title)

            kwargs['queryset'] = SwimContentType.objects.filter(
                title__in=titles
            )

        return super(ContentSchemaMemberInline, self).formfield_for_dbfield(
                db_field, **kwargs)

#-------------------------------------------------------------------------------
class ResourceTypeMiddlewareMappingInline(admin.TabularInline):
    template = "admin/swim_tabular.html"
    model = ResourceTypeMiddlewareMapping
    extra = 0

#-------------------------------------------------------------------------------
class ResourceTypeSwimContentTypeMappingInline(admin.TabularInline):
    template = "admin/swim_tabular.html"
    model = ResourceTypeSwimContentTypeMapping
    extra = 0


#-------------------------------------------------------------------------------
class ContentSchemaAdmin(ModelAdmin):
    search_fields = (
        'title',
    )
    list_display = (
        'title',
    )
    inlines = [
        ContentSchemaMemberInline,
    ]
admin.site.register(ContentSchema, ContentSchemaAdmin)

#-------------------------------------------------------------------------------
class ResourceTypeAdmin(ModelAdmin):
    exclude = ['_swim_content_type', 'content_schema_cache']
    search_fields = (
        'parent__title',
        'key',
        'title',
    )
    list_filter = (
        'parent',
    )
    list_display = (
        'title',
        'parent',
        'key',
    )
    inlines = [
        ResourceTypeTemplateInline,
        ResourceTypeMiddlewareMappingInline,
        ResourceTypeSwimContentTypeMappingInline,
    ]

# ResourceType Administration
admin.site.register(ResourceType, ResourceTypeAdmin)

#-------------------------------------------------------------------------------
class DefaultResourceTypeMappingAdmin(ModelAdmin):
    list_display = (
        'resource_model',
        'resource_type',
    )
    # TODO: Ensure that ONLY django content types which inhert from the appropriate
    # swim models are included in the drop down.
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "resource_model":
            ids = []
            for content_type in DjangoContentType.objects.all():
                klass = content_type.model_class()
                if klass is not None and issubclass(klass, HasResourceType):
                    ids.append(content_type.pk)
            kwargs["queryset"] = DjangoContentType.objects.filter(pk__in=ids)
            return db_field.formfield(**kwargs)
        return super(DefaultResourceTypeMappingAdmin, self) \
                .formfield_for_foreignkey(db_field, request, **kwargs)

# ResourceType Administration
admin.site.register(DefaultResourceTypeMapping, DefaultResourceTypeMappingAdmin)

#-------------------------------------------------------------------------------
class ArrangementTypeMappingInline(admin.TabularInline):
    model = ArrangementTypeMapping
    extra = 0

#-------------------------------------------------------------------------------
class ArrangementTypeAdmin(ModelAdmin):
    exclude = ['_swim_content_type', 'content_schema_cache']
    search_fields = (
        'key',
        'title',
    )
    list_display = (
        'title',
        'key',
    )
    inlines = [
        ArrangementTypeMappingInline,
    ]
admin.site.register(ArrangementType, ArrangementTypeAdmin)

#-------------------------------------------------------------------------------
class EnumTypeChoiceInline(admin.TabularInline):
    model = EnumTypeChoice
    extra = 0

#-------------------------------------------------------------------------------
class EnumTypeAdmin(ModelAdmin):
    exclude = ['_swim_content_type',]
    search_fields = (
        'key',
        'title',
    )
    list_display = (
        'title',
        'key',
    )
    inlines = [
        EnumTypeChoiceInline,
    ]
admin.site.register(EnumType, EnumTypeAdmin)

