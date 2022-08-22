# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import swim.media.fields


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0002_adding_default_resource_type_mappings_to_events'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calendar',
            name='facebook_image',
            field=swim.media.fields.ImageField(help_text='\n<p><b>Facebook Image</b>: Set an image to use when this document is shared on Facebook.</p>\n', max_length=512, null=True, upload_to='content/facebook/', blank=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='facebook_image',
            field=swim.media.fields.ImageField(help_text='\n<p><b>Facebook Image</b>: Set an image to use when this document is shared on Facebook.</p>\n', max_length=512, null=True, upload_to='content/facebook/', blank=True),
        ),
    ]
