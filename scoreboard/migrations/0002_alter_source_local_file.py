# Generated by Django 3.2.8 on 2021-10-10 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scoreboard', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='local_file',
            field=models.FilePathField(path='/Users/aoei/tnnt/python-backend/xlog'),
        ),
    ]
