from xml.etree import ElementTree

import requests
import stripe
import xmltodict
from decouple import config
from django.conf import settings
from django.http.response import HttpResponse
from django.utils.translation import gettext as _
from graphql_relay import from_global_id
from members.models import Attachment as MemberAttachment
from memberships.models import Membership, MembershipPlan

from .models import Attachment, Payment, PaymentMethod


def bank_webhook(request):
    endpoint_secret = settings.BANK_WEBHOOK_SECRET
    payload = request.body
    sig_header = None
    event = None

    if 'HTTP_STRIPE_SIGNATURE' in request.META:
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    if sig_header:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
            if event['type'] == 'checkout.session.completed':
                try:
                    chechout_session = event['data']['object']

                    if chechout_session['mode'] == 'subscription':
                        if chechout_session['payment_status'] == 'paid':
                            payment = Attachment.objects.get(
                                content=chechout_session['id']).payment
                            payment.membership.attachments.get_or_create(
                                title='stripe_subscription_id',
                                content=chechout_session['subscription'])

                            payment.set_paid(_('Subscription created'))

                            return HttpResponse(status=200)

                    if chechout_session['mode'] == 'payment':
                        if chechout_session['payment_status'] == 'paid':
                            payment = Attachment.objects.get(
                                content=chechout_session['id']).payment
                            payment.set_paid(payment.description)
                            return HttpResponse(status=200)

                    return HttpResponse(status=204)
                except Exception as e:
                    return HttpResponse(content=e, status=400)

            if event['type'] == 'invoice.paid':
                try:
                    invoice = event['data']['object']
                    if invoice['billing_reason'] == 'subscription_cycle':
                        if invoice['status'] == 'paid':
                            member = MemberAttachment.objects.get(
                                content=invoice['customer']).member

                            plan_id = invoice['lines']['data'][0]['plan']['id']
                            membership_plan = MembershipPlan.objects.get(
                                ref=plan_id)

                            payment = Payment.objects.create(
                                user=member.user,
                                method=PaymentMethod.objects.get(title='ST'),
                                amount=(float(invoice['amount_paid']) / 100),
                                description='Subscription cycle',
                            )
                            payment.attachments.create(
                                title='invoice_id',
                                content=invoice['id']
                            )

                            membership = Membership.objects.create(
                                ref=Membership.STRIPE,
                                member=member,
                                membership_plan=membership_plan,
                                payment=payment,
                                is_active=True
                            )

                            membership_attachment, created = membership.attachments.get_or_create(
                                title='stripe_subscription_id'
                            )
                            membership_attachment.content = invoice['subscription']
                            membership_attachment.save()

                            membership.save()

                            payment.set_paid('Subscription cycle')

                            return HttpResponse(status=200)

                    return HttpResponse(status=204)
                except Exception as e:
                    return HttpResponse(content=e, status=400)

            if event['type'] == 'checkout.session.expired':
                try:
                    checkout_session = event['data']['object']

                    payment = Attachment.objects.get(
                        content=checkout_session['id']).payment
                    payment.set_expired('Session expired')

                    return HttpResponse(status=200)
                except Exception as e:
                    return HttpResponse(content=e, status=400)

            return HttpResponse(status=204)
        except ValueError as e:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            return HttpResponse(status=400)
        except Exception as e:
            return HttpResponse(content=e, status=400)

    if 'notificationType' in request.POST and request.POST['notificationType'] == 'transaction':
        notification_code = request.POST['notificationCode']

        url = f"https://ws.pagseguro.uol.com.br/v3/transactions/notifications/{notification_code}?email=leonunesbs.dev@gmail.com&token={config('PAGSEGURO_TOKEN')}"

        response = requests.get(url)

        string_xml = response.text
        xml_tree = ElementTree.fromstring(string_xml)

        obj = xmltodict.parse(ElementTree.tostring(
            xml_tree, encoding='utf8').decode('utf8'))

        if 'errors' in obj:
            return HttpResponse(status=400, content=obj['errors'])

        status = obj['transaction']['status']

        if status == '3':
            transaction_code = obj['transaction']['code']
            reference = obj['transaction']['reference']
            payment = Payment.objects.get(pk=from_global_id(reference)[1])
            payment.set_paid(payment.description)
            payment.attachments.create(
                title='pagseguro_transaction_code', content=transaction_code)
            return HttpResponse(status=200)

        if status == '7':
            reference = obj['transaction']['reference']
            payment = Payment.objects.get(pk=from_global_id(reference)[1])
            payment.set_expired(payment.description)
            return HttpResponse(status=200)

    return HttpResponse(status=201)
