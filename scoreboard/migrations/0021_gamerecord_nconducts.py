# Generated by Django 3.2.3 on 2021-08-06 05:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scoreboard', '0020_auto_20210806_0524'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamerecord',
            name='nconducts',
            field=models.IntegerField(default=0),
        ),
    ]
