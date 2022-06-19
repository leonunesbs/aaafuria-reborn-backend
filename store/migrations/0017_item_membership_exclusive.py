# Generated by Django 3.2.13 on 2022-06-19 22:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0016_alter_item_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='membership_exclusive',
            field=models.BooleanField(default=False, help_text='Should this item be sold only to members?'),
        ),
    ]
