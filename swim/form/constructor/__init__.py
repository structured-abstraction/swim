from django import forms

#-------------------------------------------------------------------------------
def textfield(swim_field):
    """Generates a django CharField
    """

    return forms.CharField(
        label = swim_field.label,
        required = swim_field.required,
        help_text = swim_field.help_text,
        initial = swim_field.initial
    )

#-------------------------------------------------------------------------------
def textareafield(swim_field):
    """Generates a django CharField with a Textarea widget
    """

    return forms.CharField(
        label = swim_field.label,
        required = swim_field.required,
        help_text = swim_field.help_text,
        widget = forms.widgets.Textarea,
        initial = swim_field.initial
    )

#-------------------------------------------------------------------------------
def checkboxfield(swim_field):
    """Generates a django BooleanField
    """

    return forms.BooleanField(
        label = swim_field.label,
        required = swim_field.required,
        help_text = swim_field.help_text,
        initial = swim_field.initial
    )

#-------------------------------------------------------------------------------
def imagefield(swim_field):
    """Generates a django ImageField
    """

    return forms.ImageField(
        label = swim_field.label,
        required = swim_field.required,
        help_text = swim_field.help_text,
        initial = swim_field.initial
    )

#-------------------------------------------------------------------------------
def filefield(swim_field):
    """Generates a django FileField
    """

    return forms.FileField(
        label = swim_field.label,
        required = swim_field.required,
        help_text = swim_field.help_text,
        initial = swim_field.initial
    )

#-------------------------------------------------------------------------------
def emailfield(swim_field):
    """Generates a django EmailField
    """

    return forms.EmailField(
        label = swim_field.label,
        required = swim_field.required,
        help_text = swim_field.help_text,
        initial = swim_field.initial
    )

#-------------------------------------------------------------------------------
def passwordfield(swim_field):
    """Generates a django CharField with a PasswordInput widget
    """

    return forms.CharField(
        label = swim_field.label,
        required = swim_field.required,
        help_text = swim_field.help_text,
        widget = forms.PasswordInput,
        initial = swim_field.initial
    )

#-------------------------------------------------------------------------------
def hiddenfield(swim_field):
    """Generates a django CharField with a PasswordInput widget
    """

    return forms.CharField(
        label = swim_field.label,
        required = swim_field.required,
        help_text = swim_field.help_text,
        widget = forms.HiddenInput,
        initial = swim_field.initial
    )
