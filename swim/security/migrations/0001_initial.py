# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import swim.media.fields
import swim.core.models
import swim.core.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessRestriction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', swim.core.modelfields.Path(unique=True, max_length=255, verbose_name='path')),
                ('redirect_path', models.CharField(default='/login/', help_text="If the user doesn't meet this requirement, they will be  redirected to this url.", max_length=255)),
                ('only_allow', models.CharField(default='Allow everyone.', max_length=255, choices=[('all_superusers', 'Only Allow Supers Users'), ('all_staff', 'Only Allow Staff Users'), ('all_users', 'Only Allow Logged in Users'), ('specific_groups', 'Only Allow Groups specified below.'), ('everyone', 'Allow everyone.')])),
                ('allow_groups', models.ManyToManyField(help_text='Select the groups who should have access to this path.  This option only applies if you select  "Only Allow Groups specified below." above.', related_name='access_restriction', to='auth.Group')),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('file', swim.media.fields.FileField(upload_to='content/secure/files')),
                ('description', models.TextField(null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Secure File',
                'verbose_name_plural': 'Secure Files',
            },
            bases=(models.Model, swim.core.models.ClassIsContentType),
        ),
        migrations.CreateModel(
            name='SecureFileSlot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('order', models.IntegerField()),
                ('key', swim.core.modelfields.Key(max_length=200, null=True, blank=True)),
                ('django_content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('file', models.ForeignKey(related_name='slots', to='security.File', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['order'],
                'verbose_name_plural': 'Files',
            },
        ),
        migrations.CreateModel(
            name='SslEncryption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', swim.core.modelfields.Path(unique=True, max_length=255, verbose_name='path')),
                ('force_ssl_connection', models.BooleanField(default=False, help_text='Forces the server to use an SSL encrypted connection when serving this path.')),
            ],
        ),
    ]
