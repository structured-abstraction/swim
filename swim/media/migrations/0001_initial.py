# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import swim.media.fields
import swim.core.models
import swim.media.models
import swim.core.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('file', swim.media.fields.FileField(max_length=1024, upload_to='content/file')),
                ('caption', models.CharField(max_length=1024, null=True, blank=True)),
                ('file_basename', models.CharField(max_length=1024, null=True, editable=False, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, swim.core.models.ClassIsContentType),
        ),
        migrations.CreateModel(
            name='FileSlot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('order', models.IntegerField()),
                ('key', swim.core.modelfields.Key(max_length=200, null=True, blank=True)),
                ('django_content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('file', models.ForeignKey(related_name='slots', to='media.File', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['order'],
                'verbose_name_plural': 'Files',
            },
        ),
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['name', 'id'],
                'abstract': False,
            },
            bases=(models.Model, swim.core.models.ClassIsContentType),
        ),
        migrations.CreateModel(
            name='FolderSlot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('order', models.IntegerField()),
                ('key', swim.core.modelfields.Key(max_length=200, null=True, blank=True)),
                ('django_content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('folder', models.ForeignKey(related_name='slots', to='media.Folder', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['order'],
                'verbose_name_plural': 'Folders',
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('image', swim.media.fields.ImageField(max_length=1024, upload_to=swim.media.models._image_upload)),
                ('image_basename', models.CharField(max_length=1024, null=True, editable=False, blank=True)),
                ('title', models.CharField(help_text='\n            This is optional and may appear as a tool tip when hovering over the image.\n        ', max_length=1024, null=True, blank=True)),
                ('alt', models.CharField(help_text='\n            This text should describe the contents of the image. It will be\n            used as alternative text in place of the image for situations\n            where the image is not available. This includes text only displays\n            or displays for the visually impaired. Although this text is not\n            required - we strongly recommend its use as search engines will\n            reward your page ranking when this text is in place.\n        ', max_length=1024, null=True, blank=True)),
                ('caption', models.CharField(help_text='\n            The image caption is usually displayed beside or on top of\n            the actual image used.  It is intended to contain additional\n            information about the image that will enhance its viewing.\n            It may describe the image as well, but descriptions of the\n            content of the image are best placed in the alt above.\n        ', max_length=1024, null=True, blank=True)),
                ('link_url', models.CharField(help_text='Optional Link URL', max_length=255, null=True, blank=True)),
                ('folder', models.ForeignKey(related_name='images', blank=True, to='media.Folder', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('folder__name', 'image_basename'),
                'abstract': False,
            },
            bases=(models.Model, swim.core.models.ClassIsContentType),
        ),
        migrations.CreateModel(
            name='ImageSlot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('order', models.IntegerField()),
                ('key', swim.core.modelfields.Key(max_length=200, null=True, blank=True)),
                ('django_content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('image', models.ForeignKey(related_name='slots', to='media.Image', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['order'],
                'verbose_name_plural': 'Images',
            },
        ),
        migrations.CreateModel(
            name='ImageType',
            fields=[
                ('keyedtype_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='core.KeyedType', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=('core.keyedtype',),
        ),
        migrations.CreateModel(
            name='ImageVariant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('key', swim.core.modelfields.Key(unique=True, max_length=200)),
                ('algorithm', models.CharField(max_length=255, choices=[('thumbnail', 'thumbnail'), ('crop', 'crop')])),
                ('arguments', models.CharField(default='{"width": XXX, "height": XXX}', help_text='\n                Value must be valid JSON.\n            ', max_length=255)),
                ('jit_generation', models.BooleanField(default=False, help_text='\n            If you set this to true, then this variant will only be generated\n            Just In Time. In other words, it will be generated the first time\n            it is accessed.\n            ')),
                ('image_type', models.ForeignKey(related_name='variants', to='media.ImageType', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='file',
            name='folder',
            field=models.ForeignKey(related_name='files', blank=True, to='media.Folder', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='imagevariant',
            unique_together=set([('key', 'image_type')]),
        ),
    ]
