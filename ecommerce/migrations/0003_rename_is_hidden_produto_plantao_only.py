# Generated by Django 3.2.12 on 2022-05-23 14:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0002_produto_is_active'),
    ]

    operations = [
        migrations.RenameField(
            model_name='produto',
            old_name='is_hidden',
            new_name='plantao_only',
        ),
    ]