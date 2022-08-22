"""
Provide some slightly MOAR dynamic versions of the generic inline admin stuff.
"""
from django.forms.models import BaseModelFormSet, modelformset_factory
from django.contrib.admin import widgets as admin_widgets
from django.forms import widgets
from django.utils.translation import ugettext as _
from django.conf import settings
from django.utils.safestring import mark_safe

from swim.core import string_to_key
from swim.core.models import ArrangementType


#-------------------------------------------------------------------------------
class BaseResourceFormSet(BaseModelFormSet):
    """
    A formset for SWIMs generic inline objects to a parent.
    """
    ct_field_name = "django_content_type"
    ct_fk_field_name = "object_id"

    def __init__(self,
            data=None, files=None, instance=None, save_as_new=None,
            prefix=None, queryset=None, key=None, title=None, interface=None
    ):
        self.interface = interface
        self.key = key or interface.key
        self.title = title or interface.title
        opts = self.model._meta
        self.instance = instance

        # Django 1.0.2 uses rel_name for it's id definitions.
        # Django 1.0.2 uses a get_default_prefix as described below.
        # we override both.
        self.rel_name = self.get_default_prefix() + "-" + self.key

        # Working around django's stupidity YET AGAIN.
        # Django will call the below "get_default_prefix" as a class method before instantiating
        # the class and then will pass in the prefix to the instantiated class - which is stupid!
        # why not just have the damned class call a member method called "get_default_prefix" in
        # the constructor when the prefix hasn't been specified.  In any case, the resulting prefix
        # that is passed in will be in one of three forms:
        # 1. prefix==None
        # 2. prefix==self.get_default_prefix()
        # 3. prefix==self.get_default_prefix() + "-" + some_arbitrary_count.
        # In ANY of those cases we want to replace the prefix with our own that uses the 'key'
        default_prefix = self.get_default_prefix()
        prefix_without_count = None
        if prefix:
            prefix_without_count = "-".join(prefix.rsplit("-")[:-1])

        if not prefix \
           or prefix == default_prefix \
           or prefix_without_count == default_prefix:
            prefix = self.get_default_prefix() + "-" + self.key

        super(BaseResourceFormSet, self).__init__(
            data=data, files=files,
            prefix=prefix, queryset=queryset
        )

    #@classmethod
    def get_default_prefix(cls):
        opts = cls.model._meta
        return '-'.join((opts.app_label, opts.object_name.lower(),
                        cls.ct_field.name, cls.ct_fk_field.name,
        ))
    get_default_prefix = classmethod(get_default_prefix)

    def get_queryset(self):
        if not hasattr(self, '_queryset'):
            # Avoid a circular import.
            from django.contrib.contenttypes.models import ContentType as DjangoContentType
            if self.instance is None:
                return self.model._default_manager.none()
            self._queryset = self.model._default_manager.filter(**{
                self.ct_field.name: DjangoContentType.objects.get_for_model(self.instance),
                self.ct_fk_field.name: self.instance.pk,
                'key':self.key,
            }).distinct()
        return self._queryset

    def save_new(self, form, commit=True):
        # Avoid a circular import.
        from django.contrib.contenttypes.models import DjangoContentType
        new_obj = form.save(commit=commit)
        setattr(new_obj, self.ct_field.get_attname(), DjangoContentType.objects.get_for_model(self.instance).pk)
        setattr(new_obj, self.ct_fk_field.get_attname(), self.instance.pk)
        new_obj.save(commit=commit)
        return new_obj

#-------------------------------------------------------------------------------
class SingleResourceFormSet(BaseResourceFormSet):
    def save_existing(self, form, instance, commit=True):
        instance.update_related(form)
        super(SingleResourceFormSet, self).save_existing(form, instance, commit)

    def save_new(self, form, commit=True):
        # Avoid a circular import.
        from django.contrib.contenttypes.models import ContentType as DjangoContentType
        kwargs = {
            self.ct_field.get_attname(): DjangoContentType.objects.get_for_model(self.instance).pk,
            self.ct_fk_field.get_attname(): self.instance.pk,
            'order': 1,
            'key': self.key,
        }
        new_obj = form.save(commit=False)
        for k, v in kwargs.items():
            setattr(new_obj, k, v)
        new_obj.save()
        return new_obj

#-------------------------------------------------------------------------------
class ArrangementTypeMixin:
    """
    Our templates need access to extra information for arrangements.
    """
    def arrangement_type(self):
        return ArrangementType.objects.get(_swim_content_type = self.interface.swim_content_type)

#-------------------------------------------------------------------------------
class ArrangementSingleResourceFormSet(SingleResourceFormSet, ArrangementTypeMixin):
    pass

#-------------------------------------------------------------------------------
class ListResourceFormSet(BaseResourceFormSet):
    def save_existing(self, form, instance, commit=True):
        instance.update_related(form)
        super(ListResourceFormSet, self).save_existing(form, instance, commit)

    def save_new(self, form, commit=True):
        # Avoid a circular import.
        from django.contrib.contenttypes.models import ContentType as DjangoContentType
        kwargs = {
            self.ct_field.get_attname(): DjangoContentType.objects.get_for_model(self.instance).pk,
            self.ct_fk_field.get_attname(): self.instance.pk,
            'key': self.key,
        }
        new_obj = form.save(commit=False)
        for k, v in kwargs.items():
            setattr(new_obj, k, v)
        new_obj.save()
        return new_obj

#-------------------------------------------------------------------------------
class ArrangementListResourceFormSet(ListResourceFormSet, ArrangementTypeMixin):
    pass

#-------------------------------------------------------------------------------
class ClassFactory:
    """
    Returns instances of a klass with extra __init__ parameters.
    """

    def __init__(self, klass, *args, **kwargs):
        self.klass = klass
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        # Make a copy of the keyword arguments that we were given at our
        # construction.
        our_kwargs = self.kwargs.copy()
        our_args = list(self.args[:])

        # Override them with the ones passed in
        our_kwargs.update(kwargs)
        our_args.extend(args)

        # return the new instance of the klass
        return self.klass(*our_args, **our_kwargs)

    def __getattr__(self, attrname):
        try:
            return super(ClassFactory, self).__getattr__(attrname)
        except AttributeError:
            return getattr(self.klass, attrname)


#-------------------------------------------------------------------------------
class FormSetFactory(ClassFactory):
    """
    A formset factory, use instances of this class INSTEAD of a formset class.

    We can't customize the place where Django instantiates FormSets. So, in order
    to pass along some custom data to formsets which will allow us to properly
    save and filter formsets for our resource objects, we have to pass along
    this callable INSTEAD of a formset class. Then this callable passes along
    the appropriate pieces of data to our custom formset classes.
    """

    def get_default_prefix(self):
        return self.klass.get_default_prefix()

#-------------------------------------------------------------------------------
class FormFieldFromDBFieldFactory:
    """
    A formfield factory, use instances of this class INSTEAD of a formfield_from_dbfield method.

    This class allows us to pass along custom data to the form field generation
    step which we need later on.
    """
    def __init__(self, formfield_from_dbfield, *args, **kwargs):
        self.formfield_from_dbfield = formfield_from_dbfield
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        # Make a copy of the keyword arguments that we were given at our
        # construction.
        our_kwargs = self.kwargs.copy()
        our_args = list(self.args[:])

        # Override them with the ones passed in
        our_kwargs.update(kwargs)
        our_args.extend(args)

        #return the new instance of the formset_class
        return self.formfield_from_dbfield(*our_args, **our_kwargs)


#-------------------------------------------------------------------------------
class DisabledWithHidden(widgets.HiddenInput):
    # TODO: this doesn't belong in this file.
    """
    Display a widget which displays with the disabled propery AND a hidden version.

    This allows us a slightly nicer interface for showing people that they can't
    edit the item but still submit it with the form.
    """

    def __init__(self, widget, *args, **kwargs):
        self.widget = widget
        self.widget.attrs['disabled'] = True
        super(DisabledWithHidden, self).__init__(*args, **kwargs)

    def render(self, name, value, *args, **kwargs):
        """
        """
        original_id = kwargs['attrs']['id']
        output = [super(DisabledWithHidden, self).render(name, value, *args, **kwargs)]
        kwargs['attrs']['id'] = '%s-other' % original_id
        output.append(self.widget.render(name, value, *args, **kwargs))
        return mark_safe(u''.join(output))

