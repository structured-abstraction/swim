# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def add_default_resource_type_mappings(apps, schema_editor):
    DefaultResourceTypeMapping = apps.get_model('core', 'DefaultResourceTypeMapping')
    ResourceType = apps.get_model('core', 'ResourceType')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    types = (
        ("content", "page", "default", "default"),
        ("content", "sitewidecontent", "site_wide_content", "Site-wide content"),
    )
    for ct_app_label, ct_model, rt_key, rt_title in types:
# Create the appropriate mapping for page in swim.blog.
        ct, _ = ContentType.objects.get_or_create(
            app_label=ct_app_label, model=ct_model
        )
        rt, _ = ResourceType.objects.get_or_create(key=rt_key, title=rt_title)
        try:
            DefaultResourceTypeMapping.objects.get(resource_model=ct)
        except DefaultResourceTypeMapping.DoesNotExist:
            DefaultResourceTypeMapping.objects.create(
                resource_model=ct,
                resource_type=rt,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0002_auto_20161021_1432'),
    ]

    operations = [
        migrations.RunPython(add_default_resource_type_mappings),
    ]
