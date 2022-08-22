import os
import traceback
from datetime import datetime, time, date

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.core import files
from django.core.signals import request_started, request_finished
from django.db import IntegrityError, transaction
from django.template import Context, Template as DjangoTemplate
from django.test import override_settings

import swim
from swim.test import TestCase
from swim.core.models import (
    ContentSchema,
    RequestHandlerMapping,
    Resource,
    ResourceType,
    EnumType,
    EnumTypeChoice,
)
from swim.content.tests.base import NoContentTestCase, NoTemplateTestCase
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.content.models import (
        Copy,
        Link,
        Page,
        CopySlot,
        DateSlot,
        TimeSlot,
        DateTimeSlot,
        IntegerSlot,
        InstantSlot,
        PeriodSlot,
        EnumSlot,
    )


#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class ContentTest(NoTemplateTestCase):
    #These tests make sure some default behaviour works for all content types

    #---------------------------------------------------------------------------
    def test_resource_type(self):
        #Make sure we can create a ResourceType and map a Page to it.
        content_schema = ContentSchema.objects.create(title="New Page Type")
        resource_type = ResourceType.objects.create(
            key='new_type',
            title = 'New Page Type',
            content_schema = content_schema,
        )
        path = '/test'
        page = Page.objects.create(
            path = path,
            resource_type = resource_type,
            title = 'Home',
        )

        # MUST create a Link record that goes to '/'
        link = Link.objects.get(
            url = path,
        )
        self.assertEqual(link, page.ownlink)

    #---------------------------------------------------------------------------
    def test_deleting_page_deletes_request_handler_mapping(self):
        # Test that the page both creates _AND_ deletes its RequestHandlerMapping
        path = '/test'
        # Before we creates the page, there should be 0
        self.assertEqual(
            0,
            RequestHandlerMapping.objects.filter(path=path, method='GET').count())

        # After we creates the page, there should be 1 RequestHandlerMapping
        page = Page.objects.create(
            path = path,
            title = 'Home',
        )
        self.assertEqual(
            1,
            RequestHandlerMapping.objects.filter(path=path, method='GET').count())
        self.assertEqual(
            1,
            page.request_handler_mappings.count())

        # After we delete the page, there should be 0 left.
        page.delete()
        self.assertEqual(
            0,
            RequestHandlerMapping.objects.filter(path=path, method='GET').count())
        self.assertEqual(
            0,
            page.request_handler_mappings.count())

    #---------------------------------------------------------------------------
    def test_duplicate_path_save(self):
        # A couple of times there was a wierdness saving copy in the admin where
        # we got an integrity error instead of the appropriate duplicate path
        # error message.
        user = User.objects.create(
                username="lakin2",
                is_active=True,
                is_staff=True,
                is_superuser=True,
                email='example@example.com',
            )
        user.set_password('password')
        user.save()
        self.client.login(username='lakin2', password='password')
        response = self.client.get("/admin/content/page/add/", {'resource_type':4})

        data = {
            'resource_type': ResourceType.objects.get(key="simple_page").id,
            'path': '/foo',
            'title': "Foo page title",
            'sitemap_include': 1,
            'sitemap_priority': 10,
            'sitemap_change_frequency': "yearly",
            'meta_no_follow': 1,
            'meta_no_index': 1,
            'meta_description': "",
            'meta_keywords': "",
        }
        response = self.client.post("/admin/content/page/add/?no_initial_formsets=1", data)
        self.assertNotContains(response, 'There already exists a Page with the path of:', status_code=302)

        response = self.client.post("/admin/content/page/add/?no_initial_formsets=1", data)
        self.assertContains(response, 'There already exists a Page ')

    #---------------------------------------------------------------------------
    def test_resource_type_default(self):
        # Make sure we can create a ResourceType and map a Page to it.
        path = '/test'
        page = Page.objects.create(
            path = path,
            title = 'Home',
        )

        self.assertTrue(page.resource_type is not None)

        template = Template.objects.create(
                path = path,
                body = "",
            )
        type_template = ResourceTypeTemplateMapping.objects.create(
                template=template
            )
        self.assertTrue(type_template.resource_type is not None)

# TODO: move all "resource.<type>.<key>" tests here.

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class AtomAccessorTests(NoContentTestCase, NoTemplateTestCase):

    def setUp(self):
        super(AtomAccessorTests, self).setUp()
        self.page = Page.objects.create(
            path = '/eagles',
            title = 'eagles'
        )
        self.template = Template.objects.create(
            path = '/',
            body = ''
        )
        ResourceTypeTemplateMapping.objects.create(
            template = self.template
        )
        self.render_template = Template.objects.create(
            path='/copy-template',
            body='{{ target.body }}',
            swim_content_type=IntegerSlot.swim_content_type(),
            http_content_type = 'text/html; charset=utf9',
        )
        ResourceTypeTemplateMapping.objects.create(
            template = self.render_template
        )

    #---------------------------------------------------------------------------
    def _create_keyed_slot(self, slot_model, key, **kwargs):
        return slot_model.objects.create(
                order=0,
                key=key,
                content_object=self.page,
                **kwargs
            )

    #---------------------------------------------------------------------------
    def _test_slot(self, slot_model, access_name, values, template_access, value_model=None):
        if value_model is None:
            value_model = slot_model

        self.template.body='''
            {% load swim_tags %}
            1 - {{ resource.''' + access_name + '''.one''' + template_access + ''' }}
            2 - {% render resource.''' + access_name + '''.two %}
        '''
        self.template.save()
        self.render_template.body = '{{ target' + template_access + ' }}'
        self.render_template.swim_content_type=value_model.swim_content_type()
        self.render_template.save()

        self._create_keyed_slot(slot_model, 'one', **values[0][0])
        self._create_keyed_slot(slot_model, 'two', **values[1][0])
        response = self.client.get('/eagles')
        self.assertContains(response, values[0][1])
        self.assertContains(response, values[1][1])

    #---------------------------------------------------------------------------
    def test_copy_access(self):
        copy_1 = Copy.objects.create(body="Body 1")
        copy_2 = Copy.objects.create(body="Body 2")
        copy = (
                ({ 'copy': copy_1}, 'Body 1',),
                ({ 'copy': copy_2}, 'Body 2',),
            )
        slots = self._test_slot(
            CopySlot, 'copy', copy, '.body', Copy)

    #---------------------------------------------------------------------------
    def test_date_type_access(self):
        dates = (
                ({ 'value': date(2009, 10, 1)}, '2009/10/01',),
                ({ 'value': date(2009, 10, 2)}, '2009/10/02',),
            )
        slots = self._test_slot(
            DateSlot, 'date', dates, '.value|date:"Y/m/d"')

    #---------------------------------------------------------------------------
    def test_datetime_type_access(self):
        datetimes = (
                ({'value': datetime(2009, 10, 1, 12, 0, 0)}, '2009/10/01 12:00:00',),
                ({'value': datetime(2009, 10, 1, 13, 0, 0)}, '2009/10/01 13:00:00',),
            )
        slots = self._test_slot(
            DateTimeSlot, 'datetime', datetimes, '.value|date:"Y/m/d H:i:s"')

    #---------------------------------------------------------------------------
    def test_time_type_access(self):
        times = (
                ({'value': time(12, 2, 0)}, '12:02:00',),
                ({'value': time(13, 3, 0)}, '13:03:00',),
            )
        slots = self._test_slot(
            TimeSlot, 'time', times, '.value|time:"H:i:s"')

    #---------------------------------------------------------------------------
    def test_integer_type_access(self):
        integers = (
                ({'value': 1}, '001',),
                ({'value': 2}, '002',),
            )
        slots = self._test_slot(
            IntegerSlot, 'integer', integers, '.value|stringformat:"03d"')

    #---------------------------------------------------------------------------
    def test_instant_type_access(self):
        instants = (
                [{'date': date(2009, 10, 1), 'time': time(12, 2, 0)}, '2009/10/01 12:02:00',],
                [{'date': date(2009, 10, 2), 'time': time(13, 3, 0)}, '2009/10/02 13:03:00',],
            )
        slots = self._test_slot(
            InstantSlot, 'instant', instants, '.timestamp|date:"Y/m/d H:i:s"')

        instants[0][1] = "2009/10/01"
        instants[1][1] = "2009/10/02"
        slots = self._test_slot(
            InstantSlot, 'instant', instants, '.date|date:"Y/m/d"')

        instants[0][1] = "12:02:00"
        instants[1][1] = "13:03:00"
        slots = self._test_slot(
            InstantSlot, 'instant', instants, '.time|time:"H:i:s"')

    #---------------------------------------------------------------------------
    def test_period_type_access(self):
        periods = (
                [{'start_date': date(2009, 10, 1), 'start_time': time(12, 2, 0)}, '2009/10/01 12:02:00',],
                [{'start_date': date(2009, 10, 2), 'start_time': time(13, 3, 0)}, '2009/10/02 13:03:00',],
            )
        slots = self._test_slot(
            PeriodSlot, 'period', periods, '.start_timestamp|date:"Y/m/d H:i:s"')

        periods[0][1] = "2009/10/01"
        periods[1][1] = "2009/10/02"
        slots = self._test_slot(
            PeriodSlot, 'period', periods, '.start_date|date:"Y/m/d"')

        periods[0][1] = "12:02:00"
        periods[1][1] = "13:03:00"
        slots = self._test_slot(
            PeriodSlot, 'period', periods, '.start_time|time:"H:i:s"')

    #---------------------------------------------------------------------------
    def test_enum_type_access(self):
        enum_type = EnumType.objects.create(
            key='colours',
            title='Colours',
        )
        enum_type_choice_1 = EnumTypeChoice.objects.create(
                enum_type=enum_type,
                order = 0,
                title='Yellow Title',
                value='Yellow'
            )
        enum_type_choice_2 = EnumTypeChoice.objects.create(
                enum_type=enum_type,
                order = 0,
                title='Purple Title',
                value='Purple'
            )

        enums = (
                [{'enum_type': enum_type, 'choice': enum_type_choice_1}, 'Yellow',],
                [{'enum_type': enum_type, 'choice': enum_type_choice_2}, 'Purple',],
            )
        slots = self._test_slot(
            EnumSlot, 'enum', enums, '.choice.value')
        enums[0][1] = "Yellow Title"
        enums[1][1] = "Yellow Title"
        slots = self._test_slot(
            EnumSlot, 'enum', enums, '.choice.title')

    #---------------------------------------------------------------------------
    def test_get_entity_by_enum(self):
        # First make some enum's - use a simple key like value
        # and a value with spaces and punctuation.
        enum_type = EnumType.objects.create(
            key='animals',
            title='Animals',
        )
        birds_choice = EnumTypeChoice.objects.create(
                enum_type=enum_type,
                order = 0,
                title='Birds 4eva',
                value='birds'
            )
        cats_choice = EnumTypeChoice.objects.create(
                enum_type=enum_type,
                order = 0,
                title='Cats ftw',
                value='Cats ftw!'
            )

        # Next, make some entities to associate them with.
        eagles_page = self.page
        crows_page = Page.objects.create(
            path = '/crows',
            title = 'crows'
        )
        hawks_page = Page.objects.create(
            path = '/hawks',
            title = 'hawks'
        )
        cats_page = Page.objects.create(
            path = '/tabby',
            title = 'tabby'
        )

        key = 'animal_type'
        eagle_type_enum = EnumSlot.objects.create(
                order=0,
                key=key,
                content_object=eagles_page,
                enum_type=enum_type,
                choice=birds_choice,
            )
        crow_type_enum = EnumSlot.objects.create(
                order=0,
                key=key,
                content_object=crows_page,
                enum_type=enum_type,
                choice=birds_choice,
            )
        hawk_type_enum = EnumSlot.objects.create(
                order=0,
                key=key,
                content_object=hawks_page,
                enum_type=enum_type,
                choice=birds_choice,
            )
        cat_type_enum = EnumSlot.objects.create(
                order=0,
                key=key,
                content_object=cats_page,
                enum_type=enum_type,
                choice=cats_choice,
            )

        self.template.body='''
            {% load swim_tags %}
            {% get_entities_by_enum where content.page.animal_type is "birds" as bird_list %}
            {% for bird in bird_list %}
                Bird:{{ bird.title }}
            {% endfor %}
            {% with "Cats ftw!" as cat_value %}
                {% get_entities_by_enum where content.page.animal_type is cat_value as cat_list %}
                {% for cat in cat_list %}
                    Cat:{{ cat.title }}
                {% endfor %}
            {% endwith %}
        '''
        self.template.save()

        response = self.client.get('/eagles')
        self.assertContains(response, "Bird:crows")
        self.assertContains(response, "Bird:hawks")
        self.assertContains(response, "Bird:eagles")
        self.assertNotContains(response, "Bird:tabby")

        self.assertNotContains(response, "Cat:crows")
        self.assertNotContains(response, "Cat:hawks")
        self.assertNotContains(response, "Cat:eagles")
        self.assertContains(response, "Cat:tabby")

