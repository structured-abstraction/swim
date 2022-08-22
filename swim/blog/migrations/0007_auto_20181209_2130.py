# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-10 04:30
from __future__ import unicode_literals

from django.db import migrations, models
import swim.core.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_adding_default_resource_type_mapping_for_tag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='key',
            field=swim.core.modelfields.Key(blank=True, max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='publish_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='publish_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]