# Generated by Django 3.2.12 on 2022-06-05 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='has_variations',
            field=models.BooleanField(default=False, help_text='By checking this box, size variations will be created for this item.'),
        ),
    ]