# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import swim.core.modelfields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PathRedirect',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', swim.core.modelfields.Path(max_length=255, verbose_name='path')),
                ('redirect_type', models.PositiveIntegerField(default=301, help_text='\nSee http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html for more information\non the types of redirects available.\n', choices=[(301, '301 - Moved Permanently'), (302, '302 - Found'), (303, '303 - See Other'), (307, '307 - Temporary Redirect')])),
                ('redirect_path', swim.core.modelfields.Path(max_length=255)),
            ],
            options={
                'ordering': ('path',),
                'verbose_name': 'Path Redirect',
                'verbose_name_plural': 'Path Redirects',
            },
        ),
    ]
