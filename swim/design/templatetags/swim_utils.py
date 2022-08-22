from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django import template


#-------------------------------------------------------------------------------
def escape_lookup(autoescape):
    """Does a lookup based on the autoescape status.

    Its a wonder that django doesn't do this bit for you.
    """
    if autoescape:
        return conditional_escape
    else:
        return lambda x: x


#-------------------------------------------------------------------------------
@stringfilter
def nbsp(value, autoescape=None):
    """Replaces spaces in the value witn &nbsp;

    Doesn't check to ensure that it's not jamming &nbsp's into the
    middle of tags."""
    esc = escape_lookup(autoescape)
    value = esc(value)
    return mark_safe(value.replace(" ", "&nbsp;"))
nbsp.needs_autoescape = True


#---------------------------------------------------------------------------
def get_item(d, k):
    try:
        return d.get(k)
    except AttributeError as e:
        return None


register = template.Library()
register.filter('nbsp', nbsp)
register.filter('get_item', get_item)

