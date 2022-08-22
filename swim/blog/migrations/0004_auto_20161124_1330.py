# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import swim.media.fields


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_adding_default_resource_type_mappings_to_blog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='facebook_image',
            field=swim.media.fields.ImageField(upload_to='content/facebook/', max_length=512, blank=True, help_text='\n<p><b>Facebook Image</b>: Set an image to use when this document is shared on Facebook.</p>\n', variants={}, null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='facebook_image',
            field=swim.media.fields.ImageField(upload_to='content/facebook/', max_length=512, blank=True, help_text='\n<p><b>Facebook Image</b>: Set an image to use when this document is shared on Facebook.</p>\n', variants={}, null=True),
        ),
    ]
