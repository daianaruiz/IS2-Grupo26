# Generated by Django 2.2.1 on 2019-05-19 00:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HomeSwitchHome', '0011_auto_20190518_1940'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foto',
            name='archivo',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]
