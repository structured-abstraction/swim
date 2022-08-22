from django import template
from django.template import Variable, Template, NodeList
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.conf import settings
from django.template import TemplateDoesNotExist, VariableDoesNotExist
from django.template.defaultfilters import stringfilter
from django.db.models import Q

from swim.design.models import ResourceTypeTemplateMapping
from swim.core.models import Resource
from swim.content.models import Arrangement, EnumSlot
from swim.core import is_subpath_on_path

register = template.Library()

#-------------------------------------------------------------------------------
class DebugNodeMixin:
    def _error(self, message):
        # TODO: add tests for everywhere this is used.
        if settings.DEBUG:
            return "<!-- DEBUG: %s -->" % message
        else:
            return ''


#-------------------------------------------------------------------------------
def do_if_subpath_on_path(parser, token):
    """
    Outputs the contents of the block if subpath is the parent or of path.

    Examples::

        {% if_subpath_on_path link.url request.path %}
            ...
        {% endif_subpath_on_path %}

        {% if_subpath_on_path link.url request.path %}
            ...
        {% else %}
            ...
        {% endif_subpath_on_path %}
    """
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, subpath, path  = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires two arguments" % token.contents.split()[0])
    end_tag = 'end' + tag_name
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()

    return RenderIfSubpathOnPath(subpath, path, nodelist_true, nodelist_false)

register.tag('if_subpath_on_path', do_if_subpath_on_path)


#-------------------------------------------------------------------------------
class RenderIfSubpathOnPath(template.Node):

    child_nodelists = ('nodelist_true', 'nodelist_false')

    def __init__(self, subpath, path, nodelist_true, nodelist_false):
        self.subpath, self.path = subpath, path
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false

    def render(self, context):
        subpath = Variable(self.subpath).resolve(context)
        path = Variable(self.path).resolve(context)
        if is_subpath_on_path(subpath, path):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)

#-------------------------------------------------------------------------------
def editobject(parser, token):
    """
    Defines a template tag that can be used to specify an object should
    be wrapped in our swim edit links when logged into the admin
    {% editobject obj %}
    """

    try:
        tag_name, obj = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "editobject must be of format {%% editobject OBJECT %%}"
        )

    nodelist = parser.parse(('endeditobject',))
    parser.delete_first_token()
    return EditNode(obj, nodelist)

register.tag('editobject', editobject)


#-------------------------------------------------------------------------------
class EditNode(template.Node):
    """
    wraps the given template nodelist with some additional html that puts
    edit links around the given content object's HTML output
    """
    def __init__(self, template_object, nodelist):
        self.template_object = template.Variable(template_object)
        self.nodelist = nodelist

    def render(self, context):
        html = self.nodelist.render(context)

        # Grab a short reference to the request
        request = context['request']

        # Replace the template variable with a value from the context
        content_object = self.template_object.resolve(context)
        if not content_object:
            return html

        django_content_type = DjangoContentType.objects.get_for_model(content_object)
        change_permission = '%s.change_%s' % (
            django_content_type.app_label,
            django_content_type.name
        )

        # Only show an edit link IF they are logged in,
        # AND they are allowed to change this content,
        # AND if we are NOT in the middle of a popup submission
        if request.user.is_authenticated and \
            request.user.has_perm(change_permission) and \
            request.GET.get('_admin_edit_links') and \
            '_popup' not in request.POST:

            html = """
            <fieldset id="%s-%d">
                <legend><a onclick="return showAddAnotherPopup(this);" href="/admin/%s/%s/%d/?_popup=1">Edit %s</a></legend>
                %s
            </fieldset>
            """ % (
                django_content_type.name,
                content_object.pk,
                django_content_type.app_label,
                django_content_type.model,
                content_object.pk,
                django_content_type.name,
                html
            )

        return html


#-------------------------------------------------------------------------------
def get_resource(parser, token):
    """Template tag: {% get_resource for RESOURCE_OBJ as VARIABLE %}

    Given any object in a django project, this tag will return the same
    object wrapped as a resource.

    DEPRECATED
    """

    error_string = "%r tag must be of format \
{%% get_resource for OBJECT as VARIABLE %%}" % token.contents.split()[0]
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(error_string)
    if len(split) == 5:
        return GetResourceNode(split[2], split[4])
    else:
        raise template.TemplateSyntaxError(error_string)

register.tag('get_resource', get_resource)


#-------------------------------------------------------------------------------
class GetResourceNode(template.Node):
    """
    DEPRECATED
    """
    def __init__(self, content_object, context_name):
        self.content_object = template.Variable(content_object)
        self.context_name = context_name

    def render(self, context):
        resource = self.content_object.resolve(context)
        if not resource:
            return resource
        if not isinstance(resource, Resource) and not isinstance(resource, Arrangement):
            return resource

        wrapped = resource

        context[self.context_name] = wrapped
        return ''


#-------------------------------------------------------------------------------
def render(parser, token):
    """Template tag: {% render SWIM_CONTENT_OBJECT %}

    Given any swim content object, this tag will look up the appropriate template
    for this object and render it using that template.
    """

    error_string = "%r tag must be of format \
{%% render OBJECT %%}" % token.contents.split()[0]
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(error_string)

    if len(split) == 2:
        return RenderNode(split[1])
    else:
        raise template.TemplateSyntaxError(error_string)

register.tag('render', render)


#-------------------------------------------------------------------------------
class RenderNode(template.Node, DebugNodeMixin):
    def __init__(self, sco_name):
        self.sco_name = sco_name
        self.sco_variable = template.Variable(sco_name)

    def render(self, context):
        resource = context.get('resource')
        if not resource:
            return self._error("No resource in context")

        request = context.get('request')
        if not request:
            return self._error("No request in context")
        try:
            sco = self.sco_variable.resolve(context)
        except VariableDoesNotExist:
            return self._error("%s not in context" % self.sco_name)

        if not sco:
            return self._error("No %s in context" % self.sco_name)

        if isinstance(sco, (tuple, list)):
            html = []
            for instance in sco:
                html += self._render_single(instance, resource, request, context)
            return ''.join(html)
        else:
            return self._render_single(sco, resource, request, context)


    def _render_single(self, sco, resource, request, context):
        try:
            types = getattr(request, 'types', {})
            resource_type_templates = getattr(
                    request, 'resource_type_templates', {}
                ).setdefault(
                    resource.resource_type.id, {}
                )

            rt_cot = None
            template = None

            # If this object is typed, we'll use that type information.
            if hasattr(sco, 'type_field_name'):
                type_id = getattr(sco, '%s_id' % sco.type_field_name, None)
                type = types.get(type_id, None)
                if not type:
                    type = getattr(sco, sco.type_field_name, None)

                if type:
                    types[type.id] = type
                    rt_cot = type.swim_content_type()

            sco_cot = sco.swim_content_type()

            if rt_cot:
                template = resource_type_templates.get(rt_cot, None)

            if not template:
                template = resource_type_templates.get(sco_cot, None)

            if not template:
                try:

                    # First try to get a template based on the resource_type
                    # swim swim_content_type
                    template = ResourceTypeTemplateMapping.get_template(
                            request,
                            resource_type=resource.resource_type,
                            swim_content_type=rt_cot,
                            http_content_type=request.http_content_type,
                        )
                    resource_type_templates[rt_cot] = template

                except TemplateDoesNotExist:
                    # If we couldn't find one that way, look for one
                    # based on the SCO's direct content_objec_type.
                    template = ResourceTypeTemplateMapping.get_template(
                            request,
                            resource_type=resource.resource_type,
                            swim_content_type = sco_cot,
                            http_content_type=request.http_content_type,
                        )
                    resource_type_templates[sco_cot] = template

            template = Template(template.template.body)

            # Check to make sure that we are allowed to render this piece of
            # content with this template.
            try:
                if request.recursion_guard_dict[(
                    sco.__class__,
                    sco.id,
                    request.path,
                    request.http_content_type,
                    sco.swim_content_type()
                )]:
                    # TODO: Figure out what to do when we hit the template recursion depth
                    raise RuntimeError('maximum recursion depth exceeded')
            except KeyError as e:
                # treat this as a False return
                pass

            # Mark this target / template combination as un-renderable
            request.recursion_guard_dict[(
                sco.__class__,
                sco.id,
                request.path,
                request.http_content_type,
                sco.swim_content_type()
            )] = True

            # Normally this would be better served with a
            # context.get('target', None) call, but django context objects
            # overload the get function to behave differently from a standard dictionary.
            # It would be unclear which 'target' we would get back from a get call as
            # there are multiple instances if we use the get / update functions.
            # Hence, we have to use the __getitem__ and __setitem__ functions which behave
            # more like the standard dictionaries
            try:
                target = context['target']
            except KeyError as e:
                target = None

            # set the name 'target' to be our content object.
            context['target'] = sco

            html = template.render(context)

            # restore whatever 'target' used to be
            context['target'] = target

            # Mark this target / template as renderable again
            request.recursion_guard_dict[(
                sco.__class__,
                sco.id,
                request.path,
                request.http_content_type,
                sco.swim_content_type()
            )] = False
            return html
        except TemplateDoesNotExist as e:
            return self._error("No template found.")


#-------------------------------------------------------------------------------
def get_entities_by_enum(parser, token):
    """{% get_entities_by_enum where APP_LABEL.MODEL.ENUM_KEY is "VALUE WITH SPACES" as CONTEXT_KEY %}

    {% get_entities_by_enum where festival.sponsor.sponsor_type is "friends" %}

    Given any content type in a django project, this tag will return a list of
    all instances which have related enum values equal to the VALUE given, and
    keyed on the ENUM_KEY value.
    """
    error_string = "%r tag must be of format " \
            "{%% %s where APP_LABEL.MODEL.ENUM_KEY is \"VALUE\" as CONTEXT_KEY %%}" % (
        token.contents.split()[0],
        token.contents.split()[0],
    )
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(error_string)
    if len(split) == 7:
        if split[1] != "where" or split[3] != "is" or split[5] != "as":
            raise template.TemplateSyntaxError(error_string)

        app_label_name = split[2]
        content_type_parts = app_label_name.split(".")
        if len(content_type_parts) != 3:
            raise template.TemplateSyntaxError(error_string)
        content_type = {
            'app_label': content_type_parts[0],
            'model': content_type_parts[1],
            'key': content_type_parts[2],
        }

        return EntityListByEnumNode(content_type, split[4],  split[6])
    else:
        raise template.TemplateSyntaxError(error_string)

register.tag('get_entities_by_enum', get_entities_by_enum)


#-------------------------------------------------------------------------------
class EntityListByEnumNode(template.Node, DebugNodeMixin):
    def __init__(self, content_type, enum_value, context_key):
        ct = self.content_type = content_type
        self.enum_value = template.Variable(enum_value)
        self.context_key = context_key

    def render(self, context):
        try:
            enum_value = self.enum_value.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        ct = self.content_type
        query_params = Q(
            django_content_type__model = ct['model'],
            django_content_type__app_label = ct['app_label'],
            key=ct['key'],
            choice__value=enum_value,
        )

        try:
            entity_type = DjangoContentType.objects.get(
                app_label=ct['app_label'],
                model=ct['model']
            ).model_class()
        except DjangoContentType.DoesNotExist:
            context[self.context_key] = []
            return self._error("No content type for %(app_label)s.%(model)s" % ct)

        resource_enums = EnumSlot.objects.filter(query_params)
        pks = [re.object_id for re in resource_enums]
        queryset = entity_type.objects.filter(pk__in=pks)
        if hasattr(entity_type, 'type_field_name'):
            queryset = queryset.select_related(entity_type.type_field_name)
        context[self.context_key] = queryset
        return ''


#-------------------------------------------------------------------------------
@register.filter
@stringfilter
def youtube_video_id(value):

    value = value.strip()

    if value.startswith('https://youtu.be/'):
        # https://youtu.be/AAAAAAA?t=0.01&autoplay=1
        value = value.replace('https://youtu.be/', '')
        value = value.split('?')[0]
        return value

    elif value.startswith('https://www.youtube.com/watch?v='):
        # https://www.youtube.com/watch?v=AAAAAAA&t=1
        value = value.replace('https://www.youtube.com/watch?v=', '')
        value = value.split('&')[0]
        return value

    elif value.startswith('https://youtube.com/watch?v='):
        # https://youtube.com/watch?v=AAAAAAAAAA&t=1
        value = value.replace('https://youtube.com/watch?v=', '')
        value = value.split('&')[0]
        return value

    return value


#-------------------------------------------------------------------------------
@register.filter
@stringfilter
def vimeo_video_id(value):

    value = value.strip()

    if value.startswith('https://player.vimeo.com/video/'):
        value = value.replace('https://player.vimeo.com/video/', '')
        return value

    if value.startswith('https://vimeo.com/'):
        value = value.replace('https://vimeo.com/', '')
        return value

    return value

