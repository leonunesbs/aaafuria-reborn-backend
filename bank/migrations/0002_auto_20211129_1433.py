# Generated by Django 3.2.9 on 2021-11-29 17:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Movimentacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=100)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('resolvida', models.BooleanField(default=False)),
                ('conta_destino', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transferencias_destino', to='bank.conta')),
                ('conta_origem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transferencias_origem', to='bank.conta')),
            ],
            options={
                'verbose_name': 'Movimentação',
                'verbose_name_plural': 'Movimentações',
            },
        ),
        migrations.DeleteModel(
            name='Transferencia',
        ),
    ]
