# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-08-10 01:41
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='imageslot',
            name='user_variant_crop',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='imagevariant',
            name='arguments',
            field=models.CharField(default='{"width": XXX, "height": XXX}', help_text='\n            Value must be valid JSON.\n        ', max_length=255),
        ),
        migrations.AlterField(
            model_name='imagevariant',
            name='jit_generation',
            field=models.BooleanField(default=False, help_text='\n        If you set this to true, then this variant will only be generated\n        Just In Time. In other words, it will be generated the first time\n        it is accessed.\n        '),
        ),
    ]
