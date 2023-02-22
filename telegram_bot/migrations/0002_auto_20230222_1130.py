# Generated by Django 3.2.12 on 2023-02-22 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='administrator',
            name='assignment',
        ),
        migrations.RemoveField(
            model_name='administrator',
            name='assignment1',
        ),
        migrations.RemoveField(
            model_name='administrator',
            name='assignment2',
        ),
        migrations.AddField(
            model_name='administrator',
            name='chat_id',
            field=models.IntegerField(default=1, max_length=256, verbose_name='ID чата в ТГ'),
            preserve_default=False,
        ),
    ]