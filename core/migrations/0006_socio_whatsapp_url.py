# Generated by Django 3.2.9 on 2021-12-12 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_socio_turma'),
    ]

    operations = [
        migrations.AddField(
            model_name='socio',
            name='whatsapp_url',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]