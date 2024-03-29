# Generated by Django 4.0 on 2022-02-03 22:28

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0007_alter_usergeneralinformation_matches_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usergeneralinformation',
            name='matches',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, default=list, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='usergeneralinformation',
            name='watched_profiles',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, default=list, null=True, size=None),
        ),
    ]
