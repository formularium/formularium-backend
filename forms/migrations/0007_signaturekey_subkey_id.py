# Generated by Django 3.1.4 on 2020-12-06 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0006_auto_20201205_1915'),
    ]

    operations = [
        migrations.AddField(
            model_name='signaturekey',
            name='subkey_id',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
