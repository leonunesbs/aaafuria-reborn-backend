# Generated by Django 3.2.12 on 2022-06-05 17:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0009_auto_20220531_1017'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='payment',
            options={'ordering': ['-created_at']},
        ),
    ]
