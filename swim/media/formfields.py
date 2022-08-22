from django import forms

class ImageField(forms.ImageField):
    def __init__(self, required=True, widget=None, label=None, initial=None,
                 help_text=None, error_messages=None, show_hidden_initial=False, **kwargs):
        super(ImageField, self).__init__(
                required=required,
                widget=widget,
                label=label,
                initial=initial,
                help_text=help_text,
                error_messages=error_messages,
                show_hidden_initial=show_hidden_initial,
                **kwargs
            )
