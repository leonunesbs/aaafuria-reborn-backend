# Generated by Django 3.2.12 on 2022-05-31 13:17

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0003_alter_attachment_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='attachment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
