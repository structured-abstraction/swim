# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('display_name', models.CharField(unique=True, max_length=255)),
                ('username', models.CharField(unique=True, max_length=255, editable=False)),
                ('given_name', models.CharField(max_length=255)),
                ('family_name', models.CharField(max_length=255)),
                ('postal_code', models.CharField(max_length=255, null=True, blank=True)),
                ('email_address', models.EmailField(help_text='Creating a new Member will send the new user an  email with their password.', unique=True, max_length=254)),
                ('change_password_code', models.CharField(max_length=25, null=True, blank=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
        ),
    ]
