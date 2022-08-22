import itertools

from django.template import Library
from django.template import Node, NodeList, Template, Context, Variable

register = Library()

#-------------------------------------------------------------------------------
class WithIteratorNode(Node):
    def __init__(self, itertool_func, list_vars, name, nodelist):
        self.itertool_func = itertool_func
        self.list_vars = list_vars
        self.name = name
        self.nodelist = nodelist

    def __repr__(self):
        return "<WithIteratorNode>"

    def render(self, context):
        args = []
        for list_var in self.list_vars:
            args.append(list_var.resolve(context))
        context.push()
        context[self.name] = self.itertool_func(*args)
        output = self.nodelist.render(context)
        context.pop()
        return output


#-------------------------------------------------------------------------------
VALID_ITERTOOL_FUNCS = ('chain', 'izip', 'roundrobin', 'zip',)

#-------------------------------------------------------------------------------
def do_withiterator(parser, token):
    """
    Adds a value to the context (inside of this block) for caching and easy
    access.

    For example::

        {% withiterator izip list1, list2, list3, ... as iterator  %}
            {% for item1, item2, item3 in iterator %}
                {{ item1 }}, {{ item2 }}, {{ item3 }}
            {% endfor %}
        {% endwithiterator %}
    """
    bits = list(token.split_contents())
    itertool_attr = bits[1]
    name = bits[-1]
    list_names = bits[2:-2]

    if bits[-2] != 'as':
        raise TemplateSyntaxError("%r expected format is 'izip list1, list2, list3 "
                "... as iterator'" % bits[0])

    if itertool_attr not in VALID_ITERTOOL_FUNCS:
        raise TemplateSyntaxError("%s expects one of %r"
                "second arg" % (bits[0], VALID_ITERTOOL_FUNCS))
    if itertool_attr in ['zip', 'izip']:
        itertool_func = zip
    else:
        itertool_func = getattr(itertools, itertool_attr)

    # evaluate names in list.
    list_vars = []
    for list_name in list_names:
        if list_name.endswith(','):
            list_name = list_name.rstrip(',')
        list_vars.append(parser.compile_filter(list_name))

    nodelist = parser.parse(('endwithiterator',))
    parser.delete_first_token()

    return WithIteratorNode(itertool_func, list_vars,  name, nodelist)
do_withiterator = register.tag('withiterator', do_withiterator)

#-------------------------------------------------------------------------------
def atatime(value, n):
    """
    Takes a list and returns a new iterable that gives you n elements at a time.

    Usage:
        {% for first, second in somelist|atatime:2 %}
            {{ first }}
            {{ second }}
        {% endfor %}
    """
    try:
        n = int(n)
    except ValueError:
        return value

    items = list(value)
    iterators = itertools.tee(items, n)
    sliced_iterators = []
    for c, iterator in enumerate(iterators):
        sliced_iterators.append(itertools.islice(iterator, c, None, n))


    def predicate(item):
        return item != None

    def _filter(item):
        return filter(predicate, item)

    return map(
            _filter,
            itertools.zip_longest(*sliced_iterators, fillvalue=None)
        )
atatime.is_safe = False
register.filter(atatime)
