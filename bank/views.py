import stripe
from core.models import Socio
from django.conf import settings
from django.http.response import HttpResponse
from django.utils import timezone

from .models import Conta, Movimentacao


def bank_webhook(request):
    endpoint_secret = settings.BANK_WEBHOOK_SECRET
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
        print(e)
        return HttpResponse(status=400)
    except Exception as e:
        return HttpResponse(content=e, status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        checkout_session = event['data']['object']
        socio = Socio.objects.get(
            stripe_customer_id=checkout_session['customer'])

        aaafuria = Socio.objects.get(user__username="22238742")

        Conta.objects.get_or_create(socio=aaafuria)[0].save()
        conta, _ = Conta.objects.get_or_create(socio=socio)
        conta.save()

        if checkout_session['mode'] == 'subscription':
            movimentacao = Movimentacao.objects.create(
                conta_origem=conta,
                conta_destino=aaafuria.conta,
                descricao=f'ASSOCIAÇÃO DE [{socio.apelido}] PARA [{aaafuria.apelido}] | MODE: {checkout_session["mode"]}',
                valor=checkout_session['amount_total']/100.00,
                resolvida=True,
                resolvida_em=timezone.now()
            )
            movimentacao.save()

        else:
            movimentacao = Movimentacao.objects.create(
                conta_origem=conta,
                conta_destino=aaafuria.conta,
                descricao=f'PAGAMENTO DE [{socio.apelido}] PARA [{aaafuria.apelido}] | MODE: {checkout_session["mode"]}',
                valor=checkout_session['amount_total']/100.00,
                resolvida=True,
                resolvida_em=timezone.now()
            )
            movimentacao.save()

    return HttpResponse(status=200)
