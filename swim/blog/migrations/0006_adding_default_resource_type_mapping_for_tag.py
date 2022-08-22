# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

#-------------------------------------------------------------------------------
def add_default_resource_type_mapping_for_tag(apps, schema_editor):
    DefaultResourceTypeMapping = apps.get_model('core', 'DefaultResourceTypeMapping')
    ResourceType = apps.get_model('core', 'ResourceType')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    ct, _ = ContentType.objects.get_or_create(**{
        'app_label': 'blog', 'model': 'tag',
    })
    rt, _ = ResourceType.objects.get_or_create(**{
        'key': 'tag', 'title': 'Blog Tag Page',
    })

    try:
        DefaultResourceTypeMapping.objects.get(resource_model=ct)
    except DefaultResourceTypeMapping.DoesNotExist:
        DefaultResourceTypeMapping.objects.create(**{
            'resource_model': ct,
            'resource_type': rt,
        })

#-------------------------------------------------------------------------------
class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_auto_20181209_1724')
    ]

    operations = [
        migrations.RunPython(add_default_resource_type_mapping_for_tag, migrations.RunPython.noop),
    ]
