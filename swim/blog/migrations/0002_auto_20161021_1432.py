# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
        ('content', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='resource_type',
            field=models.ForeignKey(related_name='post_set', blank=True, to='core.ResourceType', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='blogyear',
            name='blog',
            field=models.ForeignKey(related_name='year_set', to='blog.Blog', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='blogyear',
            name='resource_type',
            field=models.ForeignKey(related_name='blogyear_set', blank=True, to='core.ResourceType', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='blogmonth',
            name='resource_type',
            field=models.ForeignKey(related_name='blogmonth_set', blank=True, to='core.ResourceType', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='blogmonth',
            name='year',
            field=models.ForeignKey(related_name='month_set', to='blog.BlogYear', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='blogday',
            name='month',
            field=models.ForeignKey(related_name='months', to='blog.BlogMonth', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='blogday',
            name='resource_type',
            field=models.ForeignKey(related_name='blogday_set', blank=True, to='core.ResourceType', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='blog',
            name='ownlink',
            field=models.ForeignKey(related_name='blog_set', blank=True, editable=False, to='content.Link', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='blog',
            name='resource_type',
            field=models.ForeignKey(related_name='blog_set', blank=True, to='core.ResourceType', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='post',
            unique_together=set([('blog', 'publish_date', 'title')]),
        ),
    ]
