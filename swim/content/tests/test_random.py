from swim.test import TestCase
from django.test import override_settings
from django.template import Context, Template

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class RandomTemplateTests(TestCase):
    """A suite of tests for exercising the random template tags.
    """

    #---------------------------------------------------------------------------
    def test_random_cycle_basic(self):
        t = Template("""
                {% load random_tags %}
                {% for time in times %}
                    {% random_cycle "one" "two" "three" "four" "five" %}
                {% endfor %}
        """)

        c = Context({"times": range(5)})
        template_contents = t.render(c)
        self.assertEqual(template_contents.count("one"), 1)
        self.assertEqual(template_contents.count("two"), 1)
        self.assertEqual(template_contents.count("three"), 1)
        self.assertEqual(template_contents.count("four"), 1)
        self.assertEqual(template_contents.count("five"), 1)

        c = Context({"times": range(10)})
        template_contents = t.render(c)
        self.assertEqual(template_contents.count("one"), 2)
        self.assertEqual(template_contents.count("two"), 2)
        self.assertEqual(template_contents.count("three"), 2)
        self.assertEqual(template_contents.count("four"), 2)
        self.assertEqual(template_contents.count("five"), 2)

    def test_random_cycle_named(self):
        t = Template("""
                {% load random_tags %}
                {% random_cycle "one" "two" "three" "four" "five" as numbers %}
                {% random_cycle numbers %}
                {% random_cycle numbers %}
                {% random_cycle numbers %}
                {% random_cycle numbers %}
        """)

        c = Context({"times": range(5)})
        template_contents = t.render(c)
        self.assertEqual(template_contents.count("one"), 1)
        self.assertEqual(template_contents.count("two"), 1)
        self.assertEqual(template_contents.count("three"), 1)
        self.assertEqual(template_contents.count("four"), 1)
        self.assertEqual(template_contents.count("five"), 1)

    #---------------------------------------------------------------------------
    def test_random_cycle_weighted(self):
        t = Template("""
                {% load random_tags %}
                {% for time in times %}
                    {% random_cycle "hidden" "hidden" "hidden" "show" "show" %}
                {% endfor %}
        """)

        c = Context({"times": range(5)})
        template_contents = t.render(c)
        self.assertEqual(template_contents.count("hidden"), 3)
        self.assertEqual(template_contents.count("show"), 2)

        c = Context({"times": range(10)})
        template_contents = t.render(c)
        self.assertEqual(template_contents.count("hidden"), 6)
        self.assertEqual(template_contents.count("show"), 4)

    #---------------------------------------------------------------------------
    def test_random_sort(self):
        t = Template("""
                {% load random_tags %}
                {% for item in items|randomsort %}
                    {{ item }}
                {% endfor %}
        """)
        d = {"items": ["one", "two", "three", "four", "five"]}
        c = Context(d)
        template_contents = t.render(c)
        self.assertEqual(template_contents.count("one"), 1)
        self.assertEqual(template_contents.count("two"), 1)
        self.assertEqual(template_contents.count("three"), 1)
        self.assertEqual(template_contents.count("four"), 1)
        self.assertEqual(template_contents.count("five"), 1)

