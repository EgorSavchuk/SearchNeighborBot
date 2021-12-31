# Generated by Django 4.0 on 2021-12-29 18:51

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0005_alter_usergeneralinformation_watched_profiles'),
    ]

    operations = [
        migrations.AddField(
            model_name='usergeneralinformation',
            name='matches',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, null=True, size=None), default=[], size=None),
        ),
        migrations.AlterField(
            model_name='usergeneralinformation',
            name='watched_profiles',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, null=True, size=None), default=[], size=None),
        ),
    ]
