from django.core.exceptions import ObjectDoesNotExist
from django.template import TemplateDoesNotExist
from django.db.models import Q
from django.template.loaders.base import Loader as BaseLoader

from jinja2 import loaders
from jinja2.exceptions import TemplateNotFound

from swim.design.models import Template
from django import template
from swim.core.models import Resource


#-------------------------------------------------------------------------------
def match_design_template(path, http_content_type, swim_content_type):
    """Returns a matching Template based on path, http_content_type, swim_content_type

    See: path_resolution_order and get_swim_template to see how this
    function is used. Basically you can think of this as being a yes/no test
    if a template exists on the given parameters
    """
    return Template.objects.get(
        path = path,
        http_content_type = http_content_type,
        swim_content_type = swim_content_type
    )

#-------------------------------------------------------------------------------
def load_design_template(path, http_content_type, swim_content_type):
    try:
        t = Template.objects.get(
            path = path,
            http_content_type = http_content_type,
            swim_content_type = swim_content_type
        )
    except ObjectDoesNotExist as e:
        raise TemplateDoesNotExist(path)
    return template.Template(t.body)

#-------------------------------------------------------------------------------
class DjangoStyleDesignTemplate(object):
    def __init__(self, name):
        self.name = name
        self.template_name = name

#-------------------------------------------------------------------------------
class DjangoStyleLoadDesignTemplate(BaseLoader):
    is_usable = True

    def get_template_sources(self, name):
        return [DjangoStyleDesignTemplate(name)]

    def get_contents(self, origin):
        try:
            t = Template.objects.get(
                Q(path=origin.name) &
                Q(swim_content_type=Resource.swim_content_type())
            )
        except ObjectDoesNotExist as e:
            error_msg = "Couldn't find template on path %s" % origin.name
            raise TemplateDoesNotExist(error_msg)
        return t.body
    get_template_sources.is_usable = True


#-------------------------------------------------------------------------------
class JinjaStyleLoadDesignTemplate(loaders.BaseLoader):
    is_usable = True

    def get_source(self, environment, template):
        if template == "500.jinja.html":
            error_msg = "The 500 template cannot be in the database."
            raise TemplateNotFound(error_msg)
        try:
            t = Template.objects.get(
                Q(path=template) &
                Q(swim_content_type=Resource.swim_content_type())
            )
        except ObjectDoesNotExist as e:
            error_msg = "Couldn't find template on path %s" % template
            raise TemplateNotFound(error_msg)
        return t.body, t.path, lambda: True

#-------------------------------------------------------------------------------
def jinja2_loader(template_dirs):
    return loaders.ChoiceLoader([
        JinjaStyleLoadDesignTemplate(),
        loaders.FileSystemLoader(template_dirs),
    ])

