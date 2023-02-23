# Generated by Django 3.2.12 on 2023-02-23 14:06

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0018_auto_20230223_1455'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='file',
            name='file_url',
        ),
        migrations.AlterField(
            model_name='client',
            name='end',
            field=models.DateField(blank=True, default=datetime.datetime(2023, 3, 23, 17, 6, 31, 548951), null=True, verbose_name='Дата конца тарифа'),
        ),
        migrations.AlterField(
            model_name='order',
            name='published',
            field=models.DateTimeField(default=datetime.datetime(2023, 2, 23, 17, 6, 31, 548950), verbose_name='Опубликован'),
        ),
    ]
