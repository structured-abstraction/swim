import random
from django.template import Node, Variable
from django.template import Library

register = Library()

#-------------------------------------------------------------------------------
def random_cycle_iter(iterable):
    """
    An iterator which produces an infinite list of items from the original list.

    It randomly sorts the list before each cycle and then returns every item
    once, once the original set it exhausted it randomly orders them once again
    and returns each item once again.
    """
    saved = list(iterable)
    while saved:
        random.shuffle(saved)
        for element in saved:
              yield element

#-------------------------------------------------------------------------------
# This tag was mostly stolen from Django's source - I have left it and its
# comments intact except for renaming them.
class RandomCycleNode(Node):
    def __init__(self, cyclevars, variable_name=None):
        self.cycle_iter = random_cycle_iter([Variable(v) for v in cyclevars])
        self.variable_name = variable_name

    def render(self, context):
        value = next(self.cycle_iter).resolve(context)
        if self.variable_name:
            context[self.variable_name] = value
        return value

#-------------------------------------------------------------------------------
def random_cycle(parser, token):
    """
    Cycles among the given strings in a random order each time this tag is
    encountered.

    Within a loop, cycles among the given strings each time through
    the loop::

        {% for o in some_list %}
            <tr class="{% random_cycle 'row1' 'row2' %}">
                ...
            </tr>
        {% endfor %}

    Outside of a loop, give the values a unique name the first time you call
    it, then use that name each sucessive time through::

            <tr class="{% random_cycle 'row1' 'row2' 'row3' as rowcolors %}">...</tr>
            <tr class="{% random_cycle rowcolors %}">...</tr>
            <tr class="{% random_cycle rowcolors %}">...</tr>

    You can use any number of values, separated by spaces. Commas can also
    be used to separate values; if a comma is used, the random_cycle values are
    interpreted as literal strings.
    """

    # Note: This returns the exact same node on each {% random_cycle name %} call;
    # that is, the node object returned from {% random_cycle a b c as name %} and the
    # one returned from {% random_cycle name %} are the exact same object. This
    # shouldn't cause problems (heh), but if it does, now you know.
    #
    # Ugly hack warning: This stuffs the named template dict into parser so
    # that names are only unique within each template (as opposed to using
    # a global variable, which would make random_cycle names have to be unique across
    # *all* templates.

    args = token.split_contents()

    if len(args) < 2:
        raise TemplateSyntaxError("'random_cycle' tag requires at least two arguments")

    if ',' in args[1]:
        # Backwards compatibility: {% random_cycle a,b %} or {% random_cycle a,b as foo %}
        # case.
        args[1:2] = ['"%s"' % arg for arg in args[1].split(",")]

    if len(args) == 2:
        # {% random_cycle foo %} case.
        name = args[1]
        if not hasattr(parser, '_namedCycleNodes'):
            raise TemplateSyntaxError("No named cycles in template. '%s' is not defined" % name)
        if not name in parser._namedCycleNodes:
            raise TemplateSyntaxError("Named random_cycle '%s' does not exist" % name)
        return parser._namedCycleNodes[name]

    if len(args) > 4 and args[-2] == 'as':
        name = args[-1]
        cycle_list = args[1:-2]
        random.shuffle(cycle_list)
        node = RandomCycleNode(cycle_list, name)
        if not hasattr(parser, '_namedCycleNodes'):
            parser._namedCycleNodes = {}
        parser._namedCycleNodes[name] = node
    else:
        cycle_list = args[1:]
        random.shuffle(cycle_list)
        node = RandomCycleNode(cycle_list)
    return node
random_cycle = register.tag(random_cycle)

#-------------------------------------------------------------------------------
def random_cycle_iter(iterable):
    """
    An iterator which produces an infinite list of items from the original list.

    It randomly sorts the list before each cycle and then returns every item
    once, once the original set it exhausted it randomly orders them once again
    and returns each item once again.
    """
    saved = list(iterable)
    while saved:
        random.shuffle(saved)
        for element in saved:
              yield element

#-------------------------------------------------------------------------------
# This tag was mostly stolen from Django's source - I have left it and its
# comments intact except for renaming them.
class RandomCycleNode(Node):
    def __init__(self, cyclevars, variable_name=None):
        self.cycle_iter = random_cycle_iter([Variable(v) for v in cyclevars])
        self.variable_name = variable_name

    def render(self, context):
        value = next(self.cycle_iter).resolve(context)
        if self.variable_name:
            context[self.variable_name] = value
        return value

#-------------------------------------------------------------------------------
def random_cycle(parser, token):
    """
    Cycles among the given strings in a random order each time this tag is
    encountered.

    Within a loop, cycles among the given strings each time through
    the loop::

        {% for o in some_list %}
            <tr class="{% random_cycle 'row1' 'row2' %}">
                ...
            </tr>
        {% endfor %}

    Outside of a loop, give the values a unique name the first time you call
    it, then use that name each sucessive time through::

            <tr class="{% random_cycle 'row1' 'row2' 'row3' as rowcolors %}">...</tr>
            <tr class="{% random_cycle rowcolors %}">...</tr>
            <tr class="{% random_cycle rowcolors %}">...</tr>

    You can use any number of values, separated by spaces. Commas can also
    be used to separate values; if a comma is used, the random_cycle values are
    interpreted as literal strings.
    """

    # Note: This returns the exact same node on each {% random_cycle name %} call;
    # that is, the node object returned from {% random_cycle a b c as name %} and the
    # one returned from {% random_cycle name %} are the exact same object. This
    # shouldn't cause problems (heh), but if it does, now you know.
    #
    # Ugly hack warning: This stuffs the named template dict into parser so
    # that names are only unique within each template (as opposed to using
    # a global variable, which would make random_cycle names have to be unique across
    # *all* templates.

    args = token.split_contents()

    if len(args) < 2:
        raise TemplateSyntaxError("'random_cycle' tag requires at least two arguments")

    if ',' in args[1]:
        # Backwards compatibility: {% random_cycle a,b %} or {% random_cycle a,b as foo %}
        # case.
        args[1:2] = ['"%s"' % arg for arg in args[1].split(",")]

    if len(args) == 2:
        # {% random_cycle foo %} case.
        name = args[1]
        if not hasattr(parser, '_namedCycleNodes'):
            raise TemplateSyntaxError("No named cycles in template. '%s' is not defined" % name)
        if not name in parser._namedCycleNodes:
            raise TemplateSyntaxError("Named random_cycle '%s' does not exist" % name)
        return parser._namedCycleNodes[name]

    if len(args) > 4 and args[-2] == 'as':
        name = args[-1]
        cycle_list = args[1:-2]
        random.shuffle(cycle_list)
        node = RandomCycleNode(cycle_list, name)
        if not hasattr(parser, '_namedCycleNodes'):
            parser._namedCycleNodes = {}
        parser._namedCycleNodes[name] = node
    else:
        cycle_list = args[1:]
        random.shuffle(cycle_list)
        node = RandomCycleNode(cycle_list)
    return node
random_cycle = register.tag(random_cycle)

#-------------------------------------------------------------------------------
def randomsort(value):
    """
    Takes a list of dicts, returns that list sorted by the property given in
    the argument.
    """
    items = list(value)
    random.shuffle(items)
    return items
randomsort.is_safe = False
register.filter(randomsort)
