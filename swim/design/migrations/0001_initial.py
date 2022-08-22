# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import swim.media.fields
import swim.design.models
import swim.core.models
import swim.core.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CSS',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('path', models.CharField(help_text='The css will be available on /css/&lt;path&gt;/', max_length=255)),
                ('body', models.TextField()),
            ],
            options={
                'ordering': ('path',),
                'verbose_name': 'CSS',
                'verbose_name_plural': 'CSS',
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('key', swim.core.modelfields.Key(max_length=128, unique=True, null=True, blank=True)),
                ('image', swim.media.fields.ImageField(upload_to='design/image')),
                ('alt', models.CharField(help_text='Alternate Text', max_length=200, null=True, blank=True)),
            ],
            options={
                'abstract': False,
                'permissions': (('can_edit_key', 'Can Edit Key'),),
            },
            bases=(models.Model, swim.core.models.ClassIsContentType),
        ),
        migrations.CreateModel(
            name='JavaScript',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('path', models.CharField(help_text='The javascript will be available on /js/&lt;path&gt;/', max_length=255)),
                ('body', models.TextField()),
            ],
            options={
                'ordering': ('path',),
                'verbose_name': 'JavaScript',
                'verbose_name_plural': 'JavaScript',
            },
        ),
        migrations.CreateModel(
            name='ResourceTypeTemplateMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('order', models.IntegerField(default=1)),
                ('resource_type', models.ForeignKey(default=swim.core.models.resource_type_default, to='core.ResourceType', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('path', models.CharField(max_length=100)),
                ('http_content_type', models.CharField(default='text/html; charset=utf-8', max_length=100)),
                ('body', models.TextField(verbose_name='Body')),
                ('domains', models.ManyToManyField(related_name='templates', to='sites.Site', blank=True)),
                ('swim_content_type', models.ForeignKey(related_name='template_set', default=swim.design.models.get_resource_swim_content_type, to='core.ContentType', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('path',),
                'verbose_name': 'template',
                'verbose_name_plural': 'templates',
            },
        ),
        migrations.AddField(
            model_name='resourcetypetemplatemapping',
            name='template',
            field=models.ForeignKey(to='design.Template', on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='template',
            unique_together=set([('path', 'http_content_type', 'swim_content_type')]),
        ),
    ]
