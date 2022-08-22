from django.contrib import admin
from django.conf import settings
from django.http import HttpRequest
from django.db import connection
from django.test import override_settings

from swim.test import TestCase
from swim.design.models import (
    Template,
)
from swim.core.models import (
    ContentSchema,
    ContentSchemaMember,
    ResourceType,
    ArrangementType,
    EnumType,
    EnumTypeChoice,
)
from swim.content.models import (
    Page,
    Copy,
    CopySlot,
    TextInputCopy,
    EditAreaCopy,
    Arrangement,
    DateSlot,
    DateTimeSlot,
    TimeSlot,
    InstantSlot,
    PeriodSlot,
    IntegerSlot,
)
from swim.django_admin import ResourceModelAdmin
from bs4 import BeautifulSoup

from django.test import override_settings

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class ContentSchemaMemberTests(TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        super(ContentSchemaMemberTests, self).setUp()

        self.user = self.create_and_login_superuser('lakin_admin', 'asdf')

        self.cs = ContentSchema.objects.get(title = "Simple Page")
        self.resource_type = ResourceType.objects.get(key='simple_page')
        self.arrangement_type = ArrangementType.objects.create(
            key = 'simple_type',
            title = "Simple Type",
            content_schema = self.cs,
        )

        self.header_scm = self.resource_type.content_schema.members.get(
                key='header'
            )
        self.header_scm.swim_content_type = TextInputCopy.swim_content_type()
        self.header_scm.save()
        self.footer_scm = self.resource_type.content_schema.members.get(
                key='footer'
            )
        self.footer_scm.swim_content_type = EditAreaCopy.swim_content_type()
        self.footer_scm.save()

        self.page = Page.objects.create(
                resource_type=self.resource_type,
                path='/page',
            )

        self.arrangement = Arrangement.objects.create(
                arrangement_type = self.arrangement_type,
            )

        self.no_content_schema_resource_type = ResourceType.objects.create(
                key = 'no_schema',
                title = "No Schema",
            )

        self.no_schema_page = Page.objects.create(
                resource_type=self.no_content_schema_resource_type,
                path='/page-no-schema',
            )

        #-----------------------------------------------------------------------
        # These are ALL single element copy pieces so ONLY one should be there.
        self.copy_title_list = (
                ("header", self.text_input_check,),
                ("body", self.tiny_mce_input_check,),
                ("footer", self.edit_area_input_check,),
            )

    #---------------------------------------------------------------------------
    def edit_area_input_check(self, soup, key, number):
        elems = soup.findAll(
            'textarea',
            attrs={
                'id': 'id_content-copyslot-django_content_type-object_id-%s-%s-_body' % (key, number),
                'class': 'swimEditArea',
                'rows': '10',
                'cols': '40',
            }
        )
        return elems

    #---------------------------------------------------------------------------
    def tiny_mce_input_check(self, soup, key, number):
        elems = soup.findAll(
            'textarea',
            attrs={
                'id': 'id_content-copyslot-django_content_type-object_id-%s-%s-_body' % (key, number),
                'class': 'swimTinyMCE',
                'rows': '10',
                'cols': '40',
            }
        )
        return elems

    #---------------------------------------------------------------------------
    def text_input_check(self, soup, key, number):
        elems = soup.findAll(
            'input',
            attrs={
                'id': 'id_content-copyslot-django_content_type-object_id-%s-%s-_body' % (key, number),
                'type': 'text',
                'class': 'vTextField',
            }
        )
        return elems

    #---------------------------------------------------------------------------
    def _test_simple_content_schema_interface(self, url, object=None, data={}):
        response = self.client.get(url, data=data)

        # Ensure that we have the appropriate edit inline titles are in the
        # response
        fieldset = u'<div class="inline-related swim-single-stacked " id="content-%sslot-django_content_type-object_id-%s-0">\n' \
                    '    <h3><b>%s:</b>\n' \
                    '    \n' \
                    '    \n' \
                    '  </h3>'
        for type, key, name in (
                (u'copy', u'header', u'Page Header Copy',),
                (u'copy', u'body', u'Page Body Copy',),
                (u'copy', u'footer', u'Page Footer Copy',),
                (u'menu', u'submenu', u'Page Sub-Menu',),
            ):
            self.assertContains(response, name)
            self.assertContains(response, fieldset % (type, key, name))

        #-----------------------------------------------------------------------
        # These are ALL single element copy pieces so ONLY one should be there.
        response = self.client.get(url, data=data)
        soup = BeautifulSoup(response.content, "html.parser")
        for copy_title, input_check in self.copy_title_list:
            self.assertEqual(1, len(input_check(soup, copy_title, 0)))
            self.assertEqual(0, len(input_check(soup, copy_title, 1)))
            self.assertEqual(0, len(input_check(soup, copy_title, 2)))


        # If the object is None then we are adding something, the rest of the test
        # are un-necessary.
        if object is None:
            return

        #-----------------------------------------------------------------------
        # Now we create some copy to fill those elements, and those copy
        # should show up, but ONLY the one admin interface still (because only
        # one copy is associated.
        first_copy_fmt = 'This is %s copy #1'
        second_copy_fmt = 'This is %s copy #2'
        third_copy_fmt = 'This is %s copy #3'
        for copy_title, input_check in self.copy_title_list:
            copy = Copy.objects.create(body = first_copy_fmt % copy_title)
            copy_slot = CopySlot.objects.create(
                order = 0,
                content_object = object,
                copy = copy,
                key = copy_title
            )

        #-----------------------------------------------------------------------
        # These are ALL single element copy pieces so ONLY one should be there.
        response = self.client.get(url, data=data)
        soup = BeautifulSoup(response.content, "html.parser")
        for copy_title, input_check in self.copy_title_list:
            self.assertContains(response, first_copy_fmt % copy_title)
            self.assertNotContains(response, second_copy_fmt % copy_title)
            self.assertNotContains(response, third_copy_fmt % copy_title)

            self.assertEqual(1, len(input_check(soup, copy_title, 0)))
            self.assertEqual(0, len(input_check(soup, copy_title, 1)))
            self.assertEqual(0, len(input_check(soup, copy_title, 2)))

        #-----------------------------------------------------------------------
        # Create a second round of copy at those same keys - in this case
        # we should see them both, but not third.
        for copy_title, input_check in self.copy_title_list:
            copy = Copy.objects.create(body = second_copy_fmt % copy_title)
            copy_slot = CopySlot.objects.create(
                order = 0,
                content_object = object,
                copy = copy,
                key = copy_title
            )

        #-----------------------------------------------------------------------
        # These are ALL single element copy pieces so ONLY one should be there.
        response = self.client.get(url, data=data)
        soup = BeautifulSoup(response.content, "html.parser")
        for copy_title, input_check in self.copy_title_list:
            self.assertContains(response, first_copy_fmt % copy_title)
            self.assertContains(response, second_copy_fmt % copy_title)
            self.assertNotContains(response, third_copy_fmt % copy_title)
            self.assertEqual(1, len(input_check(soup, copy_title, 0)))
            self.assertEqual(1, len(input_check(soup, copy_title, 1)))
            self.assertEqual(0, len(input_check(soup, copy_title, 2)))



        #-----------------------------------------------------------------------
        # In this case we're testing that content randomly associated with the
        # resource is still showing up in the admin.  We test this because we
        # want to ensure that when switching resource_types the pages are
        random_body = "This is random MOFO!"
        copy = Copy.objects.create(
                body = random_body,
            )
        copy_slot = CopySlot.objects.create(
            order = 0,
            content_object = object,
            copy = copy,
            key = 'random',
            _body = random_body
        )

        #-----------------------------------------------------------------------
        # These are ALL single element copy pieces so ONLY one should be there.
        response = self.client.get(url, data=data)
        soup = BeautifulSoup(response.content, "html.parser")
        for copy_title, input_check in self.copy_title_list:
            self.assertContains(response, first_copy_fmt % copy_title)
            self.assertContains(response, second_copy_fmt % copy_title)
            self.assertNotContains(response, third_copy_fmt % copy_title)
            self.assertEqual(1, len(input_check(soup, copy_title, 0)))
            self.assertEqual(1, len(input_check(soup, copy_title, 1)))
            self.assertEqual(0, len(input_check(soup, copy_title, 2)))

        # The new stuff should be as well
        self.assertContains(response, random_body)
        self.assertEqual(1, len(self.tiny_mce_input_check(soup, 'random', 0)))


    #---------------------------------------------------------------------------
    def test_Simple_Page_has_right_interface(self):
        self._test_simple_content_schema_interface(
                '/admin/content/page/%d/change/' % self.page.id,
                self.page,
            )

    #---------------------------------------------------------------------------
    def test_Simple_Page_has_right_interface_on_add(self):
        self._test_simple_content_schema_interface(
                '/admin/content/page/add/',
                data = {'type': self.resource_type.id},
            )

    #---------------------------------------------------------------------------
    def test_arrangement_has_right_interface_on_edit(self):
        self._test_simple_content_schema_interface(
                '/admin/content/arrangement/%d/change/' % self.arrangement.id,
                self.arrangement,
            )

    #---------------------------------------------------------------------------
    def test_arrangement_has_right_interface_on_add(self):
        self._test_simple_content_schema_interface(
                '/admin/content/arrangement/add/',
                data = {'type': self.arrangement_type.id}
            )

    #---------------------------------------------------------------------------
    def test_no_schema_Simple_Page_has_right_interface(self):

        response = self.client.get('/admin/content/page/%d/change/' % self.no_schema_page.id)
        self.assertEqual(200, response.status_code)

        # Ensure that we have the appropriate edit inline titles are in the
        # response
        fieldset = '<div class="inline-related swim-single-stacked last-related">\n' \
                    '  <h3>\n' \
                    '    %s\n' \
                    '    \n' \
                    '  </h3>'
        for name in (
                'Page Header Copy',
                'Page Body Copy',
                'Page Footer Copy',
                'Page Sub-Menu',
                'Page File List',
            ):
            self.assertNotContains(response, name)
            self.assertNotContains(response, fieldset % name)

    #---------------------------------------------------------------------------
    def _get_soup_for_ContentSchemaMember_type(self, key, type):
        csm = ContentSchemaMember.objects.create(
            content_schema=self.cs,
            order=10,
            key=key,
            cardinality='single',
            swim_content_type=type.swim_content_type(),
        )
        page_path = '/admin/content/page/%d/change/' % self.page.id
        response = self.client.get(page_path)

        return BeautifulSoup(response.content, "html.parser")

    #---------------------------------------------------------------------------
    def test_resource_date_interface(self):
        soup = self._get_soup_for_ContentSchemaMember_type('date', DateSlot)
        elems = soup.findAll(
            'input',
            attrs={
                'id': 'id_content-dateslot-django_content_type-object_id-date-%s-value' % (0,),
                'class': 'vDateField',
            }
        )
        self.assertEqual(1, len(elems))

    #---------------------------------------------------------------------------
    def test_resource_datetime_interface(self):
        soup = self._get_soup_for_ContentSchemaMember_type('datetime', DateTimeSlot)
        elems = soup.findAll(
            'input',
            attrs={
                'id': 'id_content-datetimeslot-django_content_type-object_id-datetime-%s-value_0' % (0,),
                'class': 'vDateField',
            }
        )
        self.assertEqual(1, len(elems))
        elems = soup.findAll(
            'input',
            attrs={
                'id': 'id_content-datetimeslot-django_content_type-object_id-datetime-%s-value_1' % (0,),
                'class': 'vTimeField',
            }
        )
        self.assertEqual(1, len(elems))

    #---------------------------------------------------------------------------
    def test_resource_time_interface(self):
        soup = self._get_soup_for_ContentSchemaMember_type('time', TimeSlot)
        elems = soup.findAll(
            'input',
            attrs={
                'id': 'id_content-timeslot-django_content_type-object_id-time-%s-value' % (0,),
                'class': 'vTimeField',
            }
        )
        self.assertEqual(1, len(elems))

    #---------------------------------------------------------------------------
    def test_resource_integer_interface(self):
        soup = self._get_soup_for_ContentSchemaMember_type('integer', IntegerSlot)
        elems = soup.findAll(
            'input',
            attrs={
                'id': 'id_content-integerslot-django_content_type-object_id-integer-%s-value' % (0,),
                'class': 'vIntegerField',
            }
        )
        self.assertEqual(1, len(elems))

    #---------------------------------------------------------------------------
    def test_resource_period_interface(self):
        soup = self._get_soup_for_ContentSchemaMember_type('period', PeriodSlot)
        elems = soup.findAll(
            'input',
            attrs={
                'id': 'id_content-periodslot-django_content_type-object_id-period-%s-start_date' % (0,),
                'class': 'vDateField',
            }
        )
        self.assertEqual(1, len(elems))
        elems = soup.findAll(
            'input',
            attrs={
                'id': 'id_content-periodslot-django_content_type-object_id-period-%s-start_time' % (0,),
                'class': 'vTimeField',
            }
        )
        self.assertEqual(1, len(elems))

        elems = soup.findAll(
            'input',
            attrs={
                'id': 'id_content-periodslot-django_content_type-object_id-period-%s-end_date' % (0,),
                'class': 'vDateField',
            }
        )
        self.assertEqual(1, len(elems))
        elems = soup.findAll(
            'input',
            attrs={
                'id': 'id_content-periodslot-django_content_type-object_id-period-%s-end_time' % (0,),
                'class': 'vTimeField',
            }
        )
        self.assertEqual(1, len(elems))

    #---------------------------------------------------------------------------
    def test_resource_instant_interface(self):
        soup = self._get_soup_for_ContentSchemaMember_type('instant', InstantSlot)
        elems = soup.findAll(
            'input',
            attrs={
                'id': 'id_content-instantslot-django_content_type-object_id-instant-%s-date' % (0,),
                'class': 'vDateField',
            }
        )
        self.assertEqual(1, len(elems))
        elems = soup.findAll(
            'input',
            attrs={
                'id': 'id_content-instantslot-django_content_type-object_id-instant-%s-time' % (0,),
                'class': 'vTimeField',
            }
        )
        self.assertEqual(1, len(elems))

    #---------------------------------------------------------------------------
    def test_enum_type_interface(self):
        enum_type = EnumType.objects.create(
            key='colours',
            title='Colours',
        )
        enum_type_choice_1 = EnumTypeChoice.objects.create(
                enum_type=enum_type,
                order = 0,
                value='Yellow',
                title='Yellow',
            )
        enum_type_choice_2 = EnumTypeChoice.objects.create(
                enum_type=enum_type,
                order = 1,
                value='Purple',
                title='Purple',
            )
        enum_type_2 = EnumType.objects.create(
            key='invalid',
            title='invalid',
        )
        enum_type_choice_3 = EnumTypeChoice.objects.create(
                enum_type=enum_type_2,
                order = 0,
                value='Magentine',
                title='Magentine',
            )

        csm = ContentSchemaMember.objects.create(
            content_schema=self.cs,
            order=10,
            key='colour',
            cardinality='single',
            swim_content_type=enum_type.swim_content_type(),
        )
        page_path = '/admin/content/page/%d/change/' % self.page.id
        response = self.client.get(page_path)
        select = """<select name="content-enumslot-django_content_type-object_id-colour-0-choice" id="id_content-enumslot-django_content_type-object_id-colour-0-choice">
<option value="" selected="selected">---------</option>
<option value="%s">Yellow</option>
<option value="%s">Purple</option>
</select>""" % (enum_type_choice_1.id, enum_type_choice_2.id)
        self.assertContains(response, select, html=True)

#-------------------------------------------------------------------------------
@override_settings(DEBUG=True, ROOT_URLCONF='swim.urls')
class ContentSchemaCachingTests(TestCase):
    """Tests which exercise the caching mechanism for content schemas.
    """

    #---------------------------------------------------------------------------
    def test_caching_of_content_schemas(self):
        content_schema = ContentSchema.objects.create(title="Test Schema")
        title_member = ContentSchemaMember.objects.create(
                content_schema=content_schema,
                order=0,
                key="title",
                title="Title",
                cardinality="single",
                swim_content_type=Copy.swim_content_type(),
            )
        rt = ResourceType.objects.create(
                key="test_page",
                title="Test Page",
                content_schema=content_schema,
            )

        rt = ResourceType.objects.get(key="test_page")
        with self.assertNumQueries(0):
            member = rt.get_interface("title")
            self.assertEqual(member['title'], "Title")
            self.assertEqual(member['cardinality'], "single")
            self.assertEqual(member['order'], 0)

        # The cache must be updated on content schema member save.
        title_member.title = "Updated Title"
        title_member.save()
        rt = ResourceType.objects.get(key="test_page")
        with self.assertNumQueries(0):
            member = rt.get_interface("title")
            self.assertEqual(member['title'], "Updated Title")
            self.assertEqual(member['cardinality'], "single")
            self.assertEqual(member['order'], 0)


