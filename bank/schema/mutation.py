import graphene
from bank.models import Attachment, Payment, PaymentMethod
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_relay import from_global_id


class CreatePayment(graphene.Mutation):
    class Arguments:
        amount = graphene.Float(required=True)
        method_id = graphene.ID(required=True)
        description = graphene.String(required=True)
        atttachment_title = graphene.String()
        attachment = Upload()
        user_username = graphene.String()

    payment = graphene.Field('bank.schema.nodes.PaymentNode')
    payment_created = graphene.Boolean()

    def mutate(self, info, method_id, atttachment_title=None, attachment=None, user_username=None, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError(_('Unauthenticated.'))
        if user.is_staff and user_username:
            user = User.objects.get(username=user_username)

        payment_method = PaymentMethod.objects.get(
            pk=from_global_id(method_id)[1])
        payment, created = Payment.objects.get_or_create(
            user=user,
            method=payment_method,
            amount=kwargs.get('amount'),
            description=kwargs.get('description'),
        )
        if created and attachment and atttachment_title:
            payment.attachments.create(
                title=kwargs.get('atttachment_title'),
                file=kwargs.get('attachment'),
            )

        return CreatePayment(payment=payment, payment_created=created)


class CheckoutUrl(graphene.Mutation):
    class Arguments:
        payment_id = graphene.ID(required=True)

    url = graphene.String()

    def mutate(self, info, payment_id):
        payment = Payment.objects.get(pk=from_global_id(payment_id)[1])
        return CheckoutUrl(url=payment.get_checkout_url())


class CreateAttachment(graphene.Mutation):
    class Arguments:
        payment_id = graphene.ID(required=True)
        title = graphene.String(required=True)
        file = Upload(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, **kwargs):
        user = info.context.user
        payment = Payment.objects.filter(
            id=from_global_id(kwargs.get('payment_id'))[1]).first()

        if not payment:
            raise GraphQLError(_('Payment not found'))

        if payment.user != user:
            if user.is_staff is False:
                raise GraphQLError(_('You are not allowed to do this action.'))

        payment.attachments.create(
            title=kwargs.get('title'),
            file=kwargs.get('file'),
        )
        payment.save()

        ok = True

        return CreateAttachment(ok=ok)


class DeleteAttachment(graphene.Mutation):
    class Arguments:
        attachment_id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, **kwargs):
        user = info.context.user
        attachment = Attachment.objects.filter(
            id=from_global_id(kwargs.get('attachment_id'))[1]).first()

        if not attachment:
            raise GraphQLError(_('Attachment not found'))

        if attachment.payment.user != user:
            if user.is_staff is False:
                raise GraphQLError(_('You are not allowed to do this action.'))

        attachment.delete()

        ok = True

        return DeleteAttachment(ok=ok)


class ConfirmPayment(graphene.Mutation):
    class Arguments:
        payment_id = graphene.ID(required=True)
        description = graphene.String(required=True)

    payment = graphene.Field('bank.schema.nodes.PaymentNode')
    ok = graphene.Boolean()

    def mutate(self, info, **kwargs):
        if not info.context.user.is_staff:
            raise GraphQLError(_('You are not allowed to do this action.'))
        payment = Payment.objects.get(
            id=from_global_id(kwargs.get('payment_id'))[1])
        payment.set_paid(kwargs.get('description'))

        return ConfirmPayment(payment=payment, ok=True)


class CancelPayment(graphene.Mutation):
    class Arguments:
        payment_id = graphene.ID(required=True)
        description = graphene.String(required=True)

    payment = graphene.Field('bank.schema.nodes.PaymentNode')
    ok = graphene.Boolean()

    def mutate(self, info, **kwargs):
        if not info.context.user.is_staff:
            raise GraphQLError(_('You are not allowed to do this action.'))
        payment = Payment.objects.get(
            id=from_global_id(kwargs.get('payment_id'))[1])
        payment.set_expired(kwargs.get('description'))

        return CancelPayment(payment=payment, ok=True)


class Mutation(graphene.ObjectType):
    create_payment = CreatePayment.Field()
    checkout_url = CheckoutUrl.Field()
    create_attachment = CreateAttachment.Field()
    delete_attachment = DeleteAttachment.Field()
    confirm_payment = ConfirmPayment.Field()
    cancel_payment = CancelPayment.Field()
