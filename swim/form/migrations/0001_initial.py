# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import swim.core.models
import swim.core.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Form',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('key', swim.core.modelfields.Key(max_length=128, unique=True, null=True, blank=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('action', swim.core.modelfields.Path(unique=True, max_length=255)),
                ('success_url', swim.core.modelfields.Path(max_length=255)),
            ],
            options={
                'abstract': False,
                'permissions': (('can_edit_key', 'Can Edit Key'),),
            },
            bases=(models.Model, swim.core.models.ClassIsContentType),
        ),
        migrations.CreateModel(
            name='FormField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('label', models.CharField(max_length=100)),
                ('help_text', models.TextField(default='', blank=True)),
                ('order', models.IntegerField()),
                ('required', models.BooleanField()),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='FormFieldArrangement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FormFieldChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('choice', models.CharField(max_length=255)),
                ('field', models.ForeignKey(to='form.FormField', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='FormFieldConstructor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('function', models.CharField(default='swim.', unique=True, max_length=100)),
                ('title', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FormFieldType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('constructor', models.ForeignKey(to='form.FormFieldConstructor', on_delete=models.CASCADE)),
                ('swim_content_type', models.ForeignKey(blank=True, editable=False, to='core.ContentType', null=True, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='FormFieldValidator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('function', models.CharField(default='swim.', unique=True, max_length=100)),
                ('title', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FormHandler',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('function', models.CharField(default='swim.', unique=True, max_length=100)),
                ('title', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FormValidator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('function', models.CharField(default='swim.', unique=True, max_length=100)),
                ('title', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='formfieldtype',
            name='validator',
            field=models.ForeignKey(to='form.FormFieldValidator', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='formfield',
            name='form',
            field=models.ForeignKey(to='form.FormFieldArrangement', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='formfield',
            name='type',
            field=models.ForeignKey(to='form.FormFieldType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='form',
            name='form_fields',
            field=models.ForeignKey(to='form.FormFieldArrangement', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='form',
            name='handler',
            field=models.ForeignKey(to='form.FormHandler', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='form',
            name='validator',
            field=models.ForeignKey(default=None, blank=True, to='form.FormValidator', null=True, on_delete=models.CASCADE),
        ),
    ]
