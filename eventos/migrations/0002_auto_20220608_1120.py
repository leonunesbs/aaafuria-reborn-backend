# Generated by Django 3.2.13 on 2022-06-08 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='evento',
            name='convidados',
            field=models.ManyToManyField(blank=True, related_name='convidados', to='eventos.Convidado'),
        ),
        migrations.AddField(
            model_name='evento',
            name='participantes',
            field=models.ManyToManyField(blank=True, to='eventos.Participante'),
        ),
    ]
