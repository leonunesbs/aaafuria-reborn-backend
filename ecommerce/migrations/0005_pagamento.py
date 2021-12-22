# Generated by Django 3.2.10 on 2021-12-22 12:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ecommerce', '0004_rename_variacaoprodutos_variacaoproduto'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pagamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('data_pagamento', models.DateTimeField(auto_now_add=True)),
                ('forma_pagamento', models.CharField(choices=[('cartao', 'Cartão de crédito'), ('especie', 'Espécie'), ('pix', 'PIX')], default='cartao', max_length=20)),
                ('carrinho', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pagamentos', to='ecommerce.carrinho')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]