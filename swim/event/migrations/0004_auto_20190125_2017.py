# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-25 20:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0003_auto_20161124_1330'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ('start_timestamp',)},
        ),
    ]
