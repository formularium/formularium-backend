# Generated by Django 3.2.2 on 2021-05-09 12:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0017_auto_20210508_1146"),
    ]

    operations = [
        migrations.DeleteModel(
            name="EncryptionKey",
        ),
    ]