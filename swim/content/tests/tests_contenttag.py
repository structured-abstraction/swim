from swim.test import TestCase
from django.template import Context, Template
from django.test import override_settings


#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class ContentTagTests(TestCase):
    """A suite of tests for exercising the the ContentTag tests.
    """

    #---------------------------------------------------------------------------
    def test_strip_font_tags(self):
        t = Template("""{% load content_tags %}{{ content|stripbadtags }}""")

        c = Context({"content": "<font>foo!</foo>"})
        template_contents = t.render(c)
        self.assertEqual(template_contents, "foo!")

    #---------------------------------------------------------------------------
    def test_strip_comments(self):
        t = Template("""{% load content_tags %}{{ content|stripbadtags }}""")

        c = Context({"content": "<!--Nothing-->foo!<!--Nothing-->"})
        template_contents = t.render(c)
        self.assertEqual(template_contents, "foo!")

    #---------------------------------------------------------------------------
    def test_strip_op_tags(self):
        t = Template("""{% load content_tags %}{{ content|stripbadtags }}""")

        c = Context({"content": "<o:p>foo!</o:p>"})
        template_contents = t.render(c)
        self.assertEqual(template_contents, "foo!")



    #---------------------------------------------------------------------------
    def test_complex_example(self):
        t = Template("""{% load content_tags %}{{ content|stripbadtags }}""")

        c = Context({"content": "<font>Bar<o:p>foo!</o:p></font>"})
        template_contents = t.render(c)
        self.assertEqual(template_contents, "Barfoo!")

        c = Context({"content": "<font>Bar<o:p>foo!</o:p><font><o:p></font>"})
        template_contents = t.render(c)
        self.assertEqual(template_contents, "Barfoo!")
