# Generated by Django 4.0 on 2021-12-23 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0002_alter_usergeneralinformation_user_tg'),
    ]

    operations = [
        migrations.AddField(
            model_name='usercriteria',
            name='required_metro',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Для совместного поиска: Рядом с какими метро хочет квартиру'),
        ),
    ]
