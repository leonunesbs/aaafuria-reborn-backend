# Generated by Django 3.2.13 on 2022-06-19 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0015_auto_20220619_1340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='image',
            field=models.ImageField(blank=True, help_text='Image ratio: 1:1', null=True, upload_to='store/images/items'),
        ),
    ]