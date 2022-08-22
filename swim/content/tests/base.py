
from swim.test import TestCase
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.media.models import (
        Image,
        File,
        ImageSlot,
    )
from swim.content.models import (
        Copy,
        Link,
        Menu,
        MenuLink,
        Arrangement,
        Page,
        ArrangementSlot,
        CopySlot,
        MenuSlot,
    )

#-------------------------------------------------------------------------------
class NoContentTestCase(TestCase):
    """
    Inherit from this class to ensure that the content database is empty.
    """

    def setUp(self):
        super(NoContentTestCase, self).setUp()

        Page.objects.all().delete()
        Copy.objects.all().delete()
        Image.objects.all().delete()
        File.objects.all().delete()
        Link.objects.all().delete()
        Menu.objects.all().delete()
        MenuLink.objects.all().delete()
        Arrangement.objects.all().delete()
        ArrangementSlot.objects.all().delete()
        CopySlot.objects.all().delete()
        MenuSlot.objects.all().delete()
        ImageSlot.objects.all().delete()

#-------------------------------------------------------------------------------
class NoTemplateTestCase(TestCase):
    """
    Inherit from this class to ensure that the template database is empty.
    """

    def setUp(self):
        super(NoTemplateTestCase, self).setUp()
        Template.objects.all().delete()
        ResourceTypeTemplateMapping.objects.all().delete()
