from swim.test import TestCase
from django.template import Context, Template
from django.test import override_settings


#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class SwimTagTests(TestCase):
    """A suite of tests for exercising SwimTags.
    """

    def test_if_subpath_on_path(self):
      t = Template("""{% load swim_tags %}{% if_subpath_on_path subpath path %}foo{% endif_subpath_on_path %}""")

      c = Context({"subpath": "/about", "path": "/about/the-team"})
      template_contents = t.render(c)
      self.assertEqual(template_contents, "foo")

    def test_if_subpath_not_on_path(self):
      t = Template("""{% load swim_tags %}{% if_subpath_on_path subpath path %}foo{% endif_subpath_on_path %}""")

      c = Context({"subpath": "/projects", "path": "/about/the-team"})
      template_contents = t.render(c)
      self.assertNotEqual(template_contents, "foo")

    def test_if_subpath_on_path_with_else(self):
      t = Template("""{% load swim_tags %}{% if_subpath_on_path subpath path %}foo{% else %}bar{% endif_subpath_on_path %}""")

      c = Context({"subpath": "/about", "path": "/about/the-team"})
      template_contents = t.render(c)
      self.assertEqual(template_contents, "foo")

    def test_if_subpath_not_on_path_with_else(self):
      t = Template("""{% load swim_tags %}{% if_subpath_on_path subpath path %}foo{% else %}bar{% endif_subpath_on_path %}""")

      c = Context({"subpath": "the-team", "path": "/about/the-team"})
      template_contents = t.render(c)
      self.assertEqual(template_contents, "bar")

    def test_if_subpath_on_path_with_nested_filter(self):
      t = Template("""{% load swim_tags %}{% if_subpath_on_path subpath path %}{{ var|upper }}{% endif_subpath_on_path %}""")
      c = Context({"subpath": "/about",
                   "path": "/about/the-team",
                   "var":"foo"})

      template_contents = t.render(c)
      self.assertEqual(template_contents, "FOO")

    def test_if_subpath_on_path_with_else_nested_filter(self):
      t = Template("""{% load swim_tags %}{% if_subpath_on_path subpath path %}foo{% else %}{{var|upper}}{% endif_subpath_on_path %}""")
      c = Context({"subpath": "/projects",
                   "path": "/about/the-team",
                   "var":"bar"})

      template_contents = t.render(c)
      self.assertEqual(template_contents, "BAR")

