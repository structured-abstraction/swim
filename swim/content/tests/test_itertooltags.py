from django.template import Template, Context
from django.test import override_settings

from swim.content.tests.base import NoTemplateTestCase

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class ItertoolTagsTest(NoTemplateTestCase):
    """A bundle of tests to exercise the Template models
    """

    def testiZip(self):
        """Test to make sure that the path store when creating a model is lower case
        """
        t = Template("""
                {% load itertool_tags %}{% spaceless %}
                {% withiterator izip list1, list2 as zipped %}
                    {% for item1, item2 in zipped %}[{{ item1 }}-{{ item2}}]{% endfor %}
                {% endwithiterator %}{% endspaceless %}
                """)
        c = Context({"list1": [1,2,3], "list2": [3,2,1]})
        self.assertEqual(
            t.render(c).strip(),
            """[1-3][2-2][3-1]""")

    def testChain(self):
        """Test to make sure that the path store when creating a model is lower case
        """
        t = Template("""
                {% load itertool_tags %}{% spaceless %}
                {% withiterator chain list1, list2 as chained %}
                    {% for item in chained %}[{{ item }}]{% endfor %}
                {% endwithiterator %}{% endspaceless %}
                """)
        c = Context({"list1": [1,2,3], "list2": [3,2,1]})
        self.assertEqual(
            t.render(c).strip(),
            """[1][2][3][3][2][1]""")

    def testiZipThree(self):
        """Test to make sure that the path store when creating a model is lower case
        """
        t = Template("""
                {% load itertool_tags %}{% spaceless %}
                {% withiterator izip list1, list2, list3 as zipped %}
                    {% for item1, item2, item3 in zipped %}[{{ item1 }}-{{ item2}}-{{item3}}]{% endfor %}
                {% endwithiterator %}{% endspaceless %}
                """)
        c = Context({"list1": [1,2,3], "list2": [3,2,1], "list3": [4,5,6]})
        self.assertEqual(
            t.render(c).strip(),
            """[1-3-4][2-2-5][3-1-6]""")

    def testChainThree(self):
        """Test to make sure that the path store when creating a model is lower case
        """
        t = Template("""
                {% load itertool_tags %}{% spaceless %}
                {% withiterator chain list1, list2, list3 as chained %}
                    {% for item in chained %}[{{ item }}]{% endfor %}
                {% endwithiterator %}{% endspaceless %}
                """)
        c = Context({"list1": [1,2,3], "list2": [3,2,1], "list3": [4,5,6]})
        self.assertEqual(
            t.render(c).strip(),
            """[1][2][3][3][2][1][4][5][6]""")

