# Generated by Django 2.2.1 on 2019-07-15 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HomeSwitchHome', '0034_delete_historialres'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='titulo_prop',
            field=models.CharField(default=None, max_length=30),
            preserve_default=False,
        ),
    ]