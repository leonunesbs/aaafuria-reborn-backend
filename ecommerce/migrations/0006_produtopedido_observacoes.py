# Generated by Django 3.2.12 on 2022-02-24 19:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0005_auto_20220204_1902'),
    ]

    operations = [
        migrations.AddField(
            model_name='produtopedido',
            name='observacoes',
            field=models.TextField(blank=True, null=True),
        ),
    ]
