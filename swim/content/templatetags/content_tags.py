import re
from django.template.defaultfilters import stringfilter
from django import template
from django.utils.safestring import mark_safe, SafeData

from bs4 import BeautifulSoup, Comment

register = template.Library()

remove_tag_list = [
    "font",
    "o:p",
    "o",
]

#-------------------------------------------------------------------------------
@register.filter(is_safe=True)
@stringfilter
def stripbadtags(html):
    """
    Removes all bad tags from the content.
    """
    soup = BeautifulSoup(html, 'html.parser')
    comments = soup.findAll(text=lambda text:isinstance(text, Comment))
    [comment.extract() for comment in comments]

    for name in remove_tag_list:
        tags = soup.find_all(re.compile(name))
        for tag in tags:
            tag.replace_with(''.join(tag.strings))

    return str(soup)


