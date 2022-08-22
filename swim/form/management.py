from django.conf import settings
from django.db import IntegrityError

from swim.core import signals
from swim.core.management import register_swim_code
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.form import models
from swim.form.models import (
    Form,
    FormFieldType,
    FormHandler,
    FormFieldConstructor,
    FormFieldValidator
)

#-------------------------------------------------------------------------------
def register_swim_form_handler(**kwargs):
    """Loads all the callable items in the list of modules given in SWIM_FORM_HANDLER_MODULES
    """
    register_swim_code(
        settings.SWIM_FORM_HANDLER_MODULES,
        FormHandler,
        ['request', 'form']
    )

signals.initialswimdata.connect(register_swim_form_handler)

#-------------------------------------------------------------------------------
def register_swim_field_constructor(**kwargs):
    """Loads all the callable items in the swim.form.constructor package
    """

    register_swim_code(
        ['swim.form.constructor',],
        FormFieldConstructor,
        ['swim_field']
    )

signals.initialswimdata.connect(register_swim_field_constructor)

#-------------------------------------------------------------------------------
def register_swim_field_validator(**kwargs):
    """Loads all the callable items in the swim.form.validator package
    """

    register_swim_code(
        ['swim.form.validator',],
        FormFieldValidator,
        ['value']
    )

signals.initialswimdata.connect(register_swim_field_validator)

#-------------------------------------------------------------------------------
form_field_types = (
    # (name, constructor_function, validation_function)
    ('text', 'swim.form.constructor.textfield', 'swim.form.validator.isValid'),
    ('textarea', 'swim.form.constructor.textareafield', 'swim.form.validator.isValid'),
    ('checkbox', 'swim.form.constructor.checkboxfield', 'swim.form.validator.isValid'),
    ('image', 'swim.form.constructor.imagefield', 'swim.form.validator.isValid'),
    ('file', 'swim.form.constructor.filefield', 'swim.form.validator.isValid'),
    ('email', 'swim.form.constructor.emailfield', 'swim.form.validator.isValid'),
    ('password', 'swim.form.constructor.passwordfield', 'swim.form.validator.isValid'),
    ('hidden', 'swim.form.constructor.hiddenfield', 'swim.form.validator.isValid'),
)
#-------------------------------------------------------------------------------
def create_standard_form_field_types(**kwargs):
    """Creates a number of default FormFieldType records.
    """
    for name, constructor_function, validation_function in form_field_types:
        # Text field
        try:
            FormFieldType.objects.create(
                name = name,
                constructor = FormFieldConstructor.objects.get(
                    function = constructor_function,
                ),
                validator = FormFieldValidator.objects.get(
                    function = validation_function,
                )
            )
        except IntegrityError as e:
            pass

signals.initialswimdata.connect(create_standard_form_field_types)




#-------------------------------------------------------------------------------
FORM_BODY = """
<div>
{% if target.form.is_multipart %}
<form enctype="multipart/form-data" method="post" action="{{ target.action }}">
{% else %}
<form method="post" action="{{ target.action }}">
{% endif %}

{% if target.form.non_field_errors %}
{{ target.form.non_field_errors }}
{% endif %}

{% for field in target.form %}
{{ field.errors }}
<p>{{ field.label }}{{ field }}</p>
{% endfor %}
<input type="submit">
</form>
</div>
"""

#-------------------------------------------------------------------------------
def create_default_form_template(**kwargs):
    """Creates a number of default FormFieldType records.
    """

    #---------------------------------------------------------------------------
    HTTP_CONTENT_TYPE = 'text/html; charset=utf-8'

    #---------------------------------------------------------------------------
    # The following definitions MUST not be run at the module level otherwise
    # they'll cause an IntegrityError because the database won't have been
    # created yet.
    FORM_SCO = Form.swim_content_type()


    template, created = Template.objects.get_or_create(
        path = '/system/default/form',
        http_content_type = HTTP_CONTENT_TYPE,
        swim_content_type = FORM_SCO,
    )

    if created:
        template.body = FORM_BODY
        template.save()

    ResourceTypeTemplateMapping.objects.get_or_create(
        template=template
    )

signals.initialswimdata.connect(create_default_form_template)

