# Generated by Django 4.1 on 2023-02-24 11:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0020_auto_20230224_0019'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='end',
            field=models.DateField(blank=True, default=datetime.datetime(2023, 3, 24, 14, 46, 52, 509014), null=True, verbose_name='Дата конца тарифа'),
        ),
        migrations.AlterField(
            model_name='order',
            name='published',
            field=models.DateTimeField(default=datetime.datetime(2023, 2, 24, 14, 46, 52, 509891), verbose_name='Опубликован'),
        ),
    ]
