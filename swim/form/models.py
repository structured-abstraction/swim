from django.db import models
from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.utils import ErrorList
from django.contrib.contenttypes.models import ContentType as DjangoContentType

from swim.core import modelfields
from swim.core.models import (
    ModelBase,
    ContentType as SwimContentType,
    Function,
    RequestHandlerMapping,
    RequestHandler,
)
from swim.core.models import KeyedModel
from swim.core.content import register_content_object

"""Defines the models for the swim.form module

There are two concepts defined in this file. The first being the concept of a
form definition. The classes that are involved are FormFieldArrangement,
FormField, and FormFieldChoice.

You can define a Form by assigning an action, success url, etc to a specific
instance of a FormFieldArrangement
"""

#-------------------------------------------------------------------------------
class FormHandler(Function):
    """Python code that can be mapped to run to handle a form submission

    def handler(form):
        pass
    """

#-------------------------------------------------------------------------------
class FormFieldConstructor(Function):
    """Python code that is responsible for returning a django form field.

    def constructor(SWIMField):
        return DjangoFormField()
    """

#-------------------------------------------------------------------------------
class FormFieldValidator(Function):
    """Python code that can be used to validate a field value

    def validator(value):
        raise ValidationError('adsf')
        return value
    """

#-------------------------------------------------------------------------------
class FormValidator(Function):
    """Python code that can be used to validate the entire form.

    def validator(cleaned_data):
        raise ValidationError('adsf')
        return cleaned_data
    """

#-------------------------------------------------------------------------------
class FormFieldArrangement(ModelBase):
    """Represents a form definition which can be used to generate a django form
    """
    name = models.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        super(FormFieldArrangement, self).__init__(*args, **kwargs)
        self._form = None
        self._request = None

    def __str__(self):
        return self.name

    def set_request(self, request):
        self._request = request

    def form(self):
        data = None
        if self._request.session.get('POST', None) and self.form:
            data = self._request.session['POST'].get(self._form.key, None)
        return self.django_form(self._request, data)

    def django_form(self, request, data={}, initial={}):
        """Returns a django form constructed from this database form definition

        Arguments:
        request - The current request that we're processing
        data - Data to bind the form to.
        """

        class FormWrapper(forms.Form):
            def __init__(self, request, *args, **kwargs):
                super(FormWrapper, self).__init__(*args, **kwargs)
                self.request = request

            def clean(self):
                super(FormWrapper, self).clean()

                # iterate over the fields and execute the validators on them.
                for name,field in self.fields.items():
                    try:
                        # Run this fields validator
                        self.cleaned_data[name] = field.validator.invoke(self.cleaned_data.get(name, None))
                    except forms.ValidationError as e:
                        errors = self._errors.get(name, None)
                        if errors is not None:
                            errors.extend(e.messages)
                        else:
                            errors = e.messages
                        self._errors[name] = errors

                # Try the form's global validation if one is provided
                swim_clean = getattr(self, 'swim_clean', None)
                if swim_clean:
                    try:
                        self.cleaned_data = swim_clean(self, self.cleaned_data)
                    except forms.ValidationError as e:
                        self._errors[NON_FIELD_ERRORS] = e.messages

                return self.cleaned_data

        # return the cached form if we already constructed it
        if self._form:
            return self._form
        if data:
            self._form = FormWrapper(request, data)
        else:
            self._form = FormWrapper(request)

        # loop over the field that should be attached to this form
        for field in self.formfield_set.all():
            field.initial = initial.get(field.name, None)
            self._form.fields[field.name] = field.type.constructor.invoke(field)
            self._form.fields[field.name].validator = field.type.validator

        return self._form

#-------------------------------------------------------------------------------
class FormFieldType(models.Model):
    """A single Form Field type that can be chosen for a form field.
    """

    name = models.CharField(max_length = 100, unique=True)
    constructor = models.ForeignKey(
        FormFieldConstructor,
        on_delete=models.CASCADE,
    )
    validator = models.ForeignKey(
        FormFieldValidator,
        on_delete=models.CASCADE,
    )
    swim_content_type = models.ForeignKey(
        SwimContentType,
        editable=False,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name

    def get_swim_content_type_title(self):
        """Returns the title of the SwimContentType that this form field type
           created a reference to when it was created.
        """
        title = "%s.%s.%s" % (
            self.__class__.__module__.rsplit('.', 1)[0],    # package
            self.__class__.__name__,
            self.name
        )
        return title

    def save(self, *args, **kwargs):
        """Create a content object type for the form field type if one doesn't
           already exist.
        """

        if not self.swim_content_type:
            self.swim_content_type = SwimContentType.objects.create(
                title = self.get_swim_content_type_title()
            )

        super(FormFieldType, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Cleans up any references to the SwimContentType record that was created
        when this model was created.
        TODO: Make this function clean up all the design and system templates that
        reference the content object type
        """
        self.swim_content_type.delete()
        super(FormFieldType, self).delete(*args, **kwargs)

#-------------------------------------------------------------------------------
class FormField(models.Model):
    """
    A single question within a form.
    """
    form = models.ForeignKey(
        FormFieldArrangement,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length = 100)
    label = models.CharField(max_length = 100)
    help_text = models.TextField(blank=True, default='')
    order = models.IntegerField()
    type = models.ForeignKey(
        FormFieldType,
        on_delete=models.CASCADE
    )
    required = models.BooleanField()
    #initial = models.CharField(
            #max_length=200,
            #help_text="The default value for this field."
        #)

    def swim_content_type(self):
        title = self.type.get_swim_content_type_title()
        try:
            swim_content_type, _ = SwimContentType.objects.get_or_create(
                title = title
            )
        except SwimContentType.DoesNotExist:
            return None
        return swim_content_type


    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', ]

#-------------------------------------------------------------------------------
class FormFieldChoice(models.Model):
    """One of a set of suggested choices for a given field.
    """
    field = models.ForeignKey(
        FormField,
        on_delete=models.CASCADE,
    )
    choice = models.CharField(max_length = 255)

    def __str__(self):
        return self.choice

#-------------------------------------------------------------------------------
class Form(KeyedModel):
    """Represents a specific instance of a FormFieldArrangement
    """

    name = models.CharField(max_length = 100, unique = True)
    action = modelfields.Path(unique = True)
    success_url = modelfields.Path()
    handler = models.ForeignKey(
        FormHandler,
        on_delete=models.CASCADE,
    )
    form_fields = models.ForeignKey(
        FormFieldArrangement,
        on_delete=models.CASCADE,
    )

    validator = models.ForeignKey(
        FormValidator,
        blank=True,
        null=True,
        default=None,
        on_delete=models.CASCADE,
    )

    def __init__(self, *args, **kwargs):
        super(Form, self).__init__(*args, **kwargs)
        self._initial = {}
        self._request = None

    def set_request(self, request):
        self._request = request

    def form(self):
        data = None
        if self._request.session.get('POST', None):
            data = self._request.session['POST'].get(self.key, None)
        return self.django_form(self._request, data)

    def field_list(self):
        data = None
        if self._request.session.get('POST', None):
            data = self._request.session['POST'].get(self.form_fields.key, None)

        field_list = []
        for django_field in self.django_form(self._request, data):
            field = self.form_fields.formfield_set.get(name = django_field.name)
            field.django_field = django_field
            field_list.append(field)
        return field_list

    def django_form(self, request, data={}):
        """Returns a django form constructed from the linked FormFieldArrangement

        Arguments:
        request - The current request that we're processing
        data - Dictionary of key value pairs to bind the form too.
        """

        django_form = self.form_fields.django_form(request, data, self._initial)
        if self.validator:
            django_form.swim_clean = self.validator.callable()
        return django_form

    def initial_data(self, initial):
        self._initial = initial

    def save(self, *args, **kwargs):
        # The path should have a slash at the end because we will be
        # posting data to it, so we can't have it redirect
        if self.action != '' and self.action is not None:
            self.action = "%s/" % self.action.rstrip('/')

        super(Form, self).save(*args, **kwargs)

        try:
            form_content_type = DjangoContentType.objects.get_for_model(self)
            request_handler = RequestHandlerMapping.objects.get(
                    django_content_type__pk=form_content_type.id,
                    object_id=self.id)
        except RequestHandlerMapping.DoesNotExist:
            request_handler = RequestHandlerMapping.objects.create(
                    content_object=self,
                    path=self.action.lower(),
                    method="POST",
                    constructor=self.get_form_view_function()
                )
        request_handler.path = self.action.lower()
        request_handler.save()

    def get_form_view_function():
        obj, _ = RequestHandler.objects.get_or_create(
                title = 'swim.form.views.FormView',
                function = 'swim.form.views.FormView',
            )
        return obj
    get_form_view_function = staticmethod(get_form_view_function)

#-------------------------------------------------------------------------------
register_content_object('form', Form)
