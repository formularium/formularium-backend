# Generated by Django 3.1.4 on 2020-12-05 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0003_signaturekey_key_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='encryptionkey',
            name='active',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]