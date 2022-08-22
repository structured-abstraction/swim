import os

from django.template import loader, TemplateDoesNotExist
from django.http import HttpRequest
from django.core import files
from django.contrib.sites.models import Site
from django.test import override_settings

import swim
from swim.content.tests.base import NoContentTestCase, NoTemplateTestCase
from swim.test import TestCase
from swim.core.models import (
    ResourceType,
)
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.content.models import (
        Copy,
        Page,
        CopySlot,
        SiteWideContent,
    )

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class SiteWideContentTests(NoTemplateTestCase):
    """A bundle of tests to exercise the Template models
    """

    def test_site_associated_content(self):
        # Test that the template access facilities allow stuff like:
        # {{ site.<key>.copy.copyright }}
        main_site = Site.objects.get_current()
        site_wide_content = SiteWideContent.objects.create(
                key = "registration",
            )
        self.copyright_copy = Copy.objects.create(
            body = 'This is the copyright 2009/09/09'
        )
        CopySlot.objects.create(
                copy = self.copyright_copy,
                order = 0,
                key = 'copyright',
                content_object = site_wide_content
            )
        self.other_copy = Copy.objects.create(
            body = 'Other Copy MofoS!'
        )
        CopySlot.objects.create(
                copy = self.other_copy,
                order = 0,
                key = 'other',
                content_object = site_wide_content
            )

        # First go around try the "copyright" copy
        self.page = Page.objects.create(
            path = '/eagles',
            title = 'eagles',
        )
        self.template = Template.objects.create(
            path = '/eagles',
            body = '{{ site.registration.copy.copyright.body }}',
            http_content_type = 'text/html; charset=utf-8'
        )
        ResourceTypeTemplateMapping.objects.create(
            template = self.template
        )
        response = self.client.get('/eagles')
        self.assertIn(self.copyright_copy.body, response.content)

        # Second go around try the "other" copy
        self.template.body = '{{ site.registration.copy.other.body }}'
        self.template.save()
        response = self.client.get('/eagles')
        self.assertIn(self.other_copy.body, response.content)

