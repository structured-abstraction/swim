# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('content', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitewidecontent',
            name='resource_type',
            field=models.ForeignKey(related_name='sitewidecontent_set', blank=True, to='core.ResourceType', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='periodslot',
            name='django_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='pageslot',
            name='django_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='pageslot',
            name='page',
            field=models.ForeignKey(related_name='slots', to='content.Page', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='page',
            name='ownlink',
            field=models.ForeignKey(related_name='page_set', blank=True, editable=False, to='content.Link', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='page',
            name='resource_type',
            field=models.ForeignKey(related_name='page_set', blank=True, to='core.ResourceType', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='menuslot',
            name='django_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='menuslot',
            name='menu',
            field=models.ForeignKey(related_name='slots', to='content.Menu', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='menulink',
            name='link',
            field=models.ForeignKey(to='content.Link', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='menulink',
            name='menu',
            field=models.ForeignKey(to='content.Menu', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='integerslot',
            name='django_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='instantslot',
            name='django_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='enumslot',
            name='choice',
            field=models.ForeignKey(to='core.EnumTypeChoice', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='enumslot',
            name='django_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='enumslot',
            name='enum_type',
            field=models.ForeignKey(editable=False, to='core.EnumType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='datetimeslot',
            name='django_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='dateslot',
            name='django_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='copyslot',
            name='copy',
            field=models.ForeignKey(related_name='slots', editable=False, to='content.Copy', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='copyslot',
            name='django_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='arrangementslot',
            name='arrangement',
            field=models.ForeignKey(related_name='slots', to='content.Arrangement', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='arrangementslot',
            name='django_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='arrangement',
            name='arrangement_type',
            field=models.ForeignKey(related_name='arrangement_set', blank=True, to='core.ArrangementType', null=True, on_delete=models.CASCADE),
        ),
    ]
