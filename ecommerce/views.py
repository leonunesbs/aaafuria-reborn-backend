from django.http.response import HttpResponse
import stripe
from django.shortcuts import render
from bank.models import Conta
from ecommerce.models import Carrinho, Pagamento
from django.conf import settings


# Stripe webhook handler
def ecommerce_webhook(request):
    endpoint_secret = settings.ECOMMERCE_WEBHOOK_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    except Exception as e:
        return HttpResponse(content=e, status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        checkout_session = event['data']['object']

        carrinho = Carrinho.objects.filter(
            stripe_checkout_id=checkout_session['id']).first()

        pagamento = Pagamento.objects.create(
            user=carrinho.user,
            carrinho=carrinho,
            status='pago',
            valor=carrinho.total,
            forma_pagamento='cartao'
        )

        carrinho.set_paid()
        carrinho.save()

        pagamento.save()

        conta, _ = Conta.objects.get_or_create(socio=carrinho.user.socio)
        conta.calangos = int(
            ((checkout_session['amount_total'] / 100) // 10) * 100)
        conta.save()

    return HttpResponse(status=200)
