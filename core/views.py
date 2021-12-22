from django.conf import settings
from django.http.response import HttpResponse
import stripe
from django.shortcuts import render
from stripe.api_resources import checkout, customer
from bank.models import Conta
from core.models import Pagamento, Socio
from datetime import datetime, timezone
from django.conf import settings


# Stripe webhook handler
def core_webhook(request):
    endpoint_secret = settings.CORE_WEBHOOK_SECRET
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
        if checkout_session['mode'] == 'subscription':

            pagamento = Pagamento.objects.filter(
                checkout_id=checkout_session['id']).first()

            pagamento.status = checkout_session['status']

            socio = pagamento.socio
            socio.is_socio = True

            # Verificar e adicionar data_inicio e data_fim
            subscription = stripe.Subscription.list(
                customer=socio.stripe_customer_id,
                status='active'
            )

            if len(subscription.data) > 0:
                if not socio.data_inicio:
                    socio.data_inicio = datetime.fromtimestamp(
                        subscription.data[0]['current_period_start'])
                socio.data_fim = datetime.fromtimestamp(
                    subscription.data[0]['current_period_end'])

                socio.stripe_subscription_id = subscription.data[0]['id']

            socio.save()
            pagamento.save()

            conta, _ = Conta.objects.get_or_create(socio=socio)
            conta.calangos = int(
                ((checkout_session['amount_total'] / 100) // 10) * 100)
            conta.save()

    # Handle the customer.subscription.deleted event
    if event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']

        socio = Socio.objects.filter(
            stripe_customer_id=subscription['customer']).first()

        socio.is_socio = False
        socio.data_fim = timezone.now()
        socio.save()

    return HttpResponse(status=200)
