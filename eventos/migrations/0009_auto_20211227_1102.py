# Generated by Django 3.2.10 on 2021-12-27 14:02

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0008_remove_ingresso_stripe_checkout_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='evento',
            name='data_fim',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='evento',
            name='data_inicio',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lote',
            name='ativo',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='lote',
            name='evento',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lotes', to='eventos.evento'),
        ),
    ]
