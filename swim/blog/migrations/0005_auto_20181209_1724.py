# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-10 00:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import swim.blog.models
import swim.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20180321_2015'),
        ('blog', '0004_auto_20161124_1330'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=64)),
                ('slug', models.SlugField(editable=False, max_length=200, null=True, unique=True, verbose_name='Path Atom')),
                ('blog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='blog.Blog')),
                ('resource_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tag_set', to='core.ResourceType')),
            ],
            options={
                'abstract': False, 'ordering': ['title'], 'verbose_name': 'Tag', 'verbose_name_plural': 'Tags',
            },
            bases=(swim.blog.models.ActsLikeTimeline, models.Model, swim.core.models.ClassIsContentType, swim.blog.models.HasPublishedTimeline),
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-publish_date'], 'verbose_name': 'Post', 'verbose_name_plural': 'Posts'},
        ),
        migrations.AddField(
            model_name='post',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='posts', to='blog.Tag', help_text='A Post must be assigned to a Blog before you can add Tags.'),
        ),
    ]
