# Generated by Django 2.2.1 on 2019-06-09 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HomeSwitchHome', '0016_auto_20190609_1303'),
    ]

    operations = [
        migrations.AddField(
            model_name='propiedad',
            name='localidad',
            field=models.CharField(default=None, max_length=30),
            preserve_default=False,
        ),
    ]
