# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import swim.core.models
import swim.core.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArrangementTypeMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ContentSchema',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(unique=True, max_length=100)),
            ],
            options={
                'ordering': ('title',),
            },
        ),
        migrations.CreateModel(
            name='ContentSchemaMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('order', models.IntegerField()),
                ('key', swim.core.modelfields.Key(max_length=100)),
                ('title', models.CharField(max_length=100)),
                ('cardinality', models.CharField(max_length=100, choices=[('single', 'single'), ('list', 'list')])),
                ('content_schema', models.ForeignKey(related_name='members', to='core.ContentSchema', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='ContentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(unique=True, max_length=255)),
            ],
            options={
                'ordering': ('title',),
            },
        ),
        migrations.CreateModel(
            name='DefaultResourceTypeMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('resource_model', models.OneToOneField(to='contenttypes.ContentType', help_text='\n        If you delete the default mapping for any particular resource model,\n        then swim will not be able to appropriately creates resources\n        of this type.  It will cause a database lookup error whenever it\n        attempts to look up the default.\n        ', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EntityType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('key', swim.core.modelfields.Key(unique=True, max_length=200)),
                ('title', models.CharField(unique=True, max_length=100)),
                ('content_schema_cache', models.TextField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EnumTypeChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('order', models.IntegerField(default=1)),
                ('title', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('order', 'value'),
            },
        ),
        migrations.CreateModel(
            name='KeyedType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('key', swim.core.modelfields.Key(unique=True, max_length=200)),
                ('title', models.CharField(unique=True, max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestHandler',
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
            name='RequestHandlerMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('object_id', models.PositiveIntegerField()),
                ('path', swim.core.modelfields.Path(max_length=255)),
                ('method', models.CharField(default='GET', max_length=10, choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('DELETE', 'DELETE'), ('HEAD', 'HEAD')])),
                ('constructor', models.ForeignKey(to='core.RequestHandler', on_delete=models.CASCADE)),
                ('django_content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='ReservedPath',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('object_id', models.PositiveIntegerField()),
                ('path', swim.core.modelfields.Path(unique=True, max_length=255)),
                ('reservation_type', models.CharField(default='single', max_length=10, choices=[('single', 'single'), ('tree', 'tree')])),
                ('django_content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ResourceTypeMiddleware',
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
            name='ResourceTypeMiddlewareMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('function', models.ForeignKey(to='core.ResourceTypeMiddleware', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='ResourceTypeResponseProcessor',
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
            name='ResourceTypeResponseProcessorMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('function', models.ForeignKey(to='core.ResourceTypeResponseProcessor', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'ResourceType ResponseProcessor Mapping',
                'verbose_name_plural': 'ResourceType ResponseProcessor Mappings',
            },
        ),
        migrations.CreateModel(
            name='ResourceTypeSwimContentTypeMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('swim_content_type', models.ForeignKey(related_name='resource_type_set', to='core.ContentType', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ArrangementType',
            fields=[
                ('entitytype_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='core.EntityType', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=('core.entitytype',),
        ),
        migrations.CreateModel(
            name='EnumType',
            fields=[
                ('keyedtype_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='core.KeyedType', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=('core.keyedtype',),
        ),
        migrations.CreateModel(
            name='ResourceType',
            fields=[
                ('entitytype_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='core.EntityType', on_delete=models.CASCADE)),
                ('parent', models.ForeignKey(default=swim.core.models.resource_type_default, blank=True, to='core.ResourceType', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['title'],
            },
            bases=('core.entitytype',),
        ),
        migrations.AddField(
            model_name='keyedtype',
            name='_swim_content_type',
            field=models.ForeignKey(blank=True, to='core.ContentType', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='entitytype',
            name='_swim_content_type',
            field=models.ForeignKey(blank=True, to='core.ContentType', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='entitytype',
            name='content_schema',
            field=models.ForeignKey(blank=True, to='core.ContentSchema', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='contentschemamember',
            name='swim_content_type',
            field=models.ForeignKey(to='core.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='arrangementtypemapping',
            name='swim_content_type',
            field=models.ForeignKey(related_name='arrangement_type_set', to='core.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='resourcetypeswimcontenttypemapping',
            name='resource_type',
            field=models.ForeignKey(related_name='adminable_set', blank=True, to='core.ResourceType', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='resourcetyperesponseprocessormapping',
            name='resource_type',
            field=models.ForeignKey(default=swim.core.models.resource_type_default, to='core.ResourceType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='resourcetypemiddlewaremapping',
            name='resource_type',
            field=models.ForeignKey(default=swim.core.models.resource_type_default, to='core.ResourceType', on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='requesthandlermapping',
            unique_together=set([('path', 'method')]),
        ),
        migrations.AddField(
            model_name='enumtypechoice',
            name='enum_type',
            field=models.ForeignKey(to='core.EnumType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='defaultresourcetypemapping',
            name='resource_type',
            field=models.ForeignKey(to='core.ResourceType', on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='contentschemamember',
            unique_together=set([('content_schema', 'key')]),
        ),
        migrations.AddField(
            model_name='arrangementtypemapping',
            name='arrangement_type',
            field=models.ForeignKey(related_name='adminable_set', blank=True, to='core.ArrangementType', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='resourcetyperesponseprocessormapping',
            unique_together=set([('resource_type', 'function')]),
        ),
        migrations.AlterUniqueTogether(
            name='resourcetypemiddlewaremapping',
            unique_together=set([('resource_type', 'function')]),
        ),
    ]
