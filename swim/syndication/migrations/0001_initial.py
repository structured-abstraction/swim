# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import swim.core.models
import swim.core.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RSSFeed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('path', swim.core.modelfields.Path(unique=True, max_length=255, verbose_name='path')),
                ('blog', models.ForeignKey(to='blog.Blog', on_delete=models.CASCADE)),
                ('resource_type', models.ForeignKey(related_name='rssfeed_set', blank=True, to='core.ResourceType', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, swim.core.models.ClassIsContentType),
        ),
    ]
