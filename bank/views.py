import stripe
from django.conf import settings
from django.http.response import HttpResponse
from django.utils.translation import gettext as _
from members.models import Attachment as MemberAttachment
from members.models import Member
from memberships.models import Attachment as MembershipAttachment
from memberships.models import Membership, MembershipPlan

from .models import Attachment, Payment, PaymentMethod


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
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)
    except Exception as e:
        return HttpResponse(content=e, status=400)

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
                    payment.set_paid(_('Payment completed'))
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
                    membership_plan = MembershipPlan.objects.get(ref=plan_id)

                    payment = Payment.objects.create(
                        user=member.user,
                        method=PaymentMethod.objects.get(title='ST'),
                        amount=invoice['amount_paid'],
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

                    membership_attachment = MembershipAttachment.objects.get_or_create(
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
