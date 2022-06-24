import graphene
from bank.models import Payment, PaymentMethod
from bank.schema.nodes import PaymentPaginatedNode
from django.utils.translation import gettext as _
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from graphql_relay import from_global_id
from utils.utils import get_paginator


class Query(graphene.ObjectType):
    payment = graphene.Field('bank.schema.nodes.PaymentNode', id=graphene.ID())
    all_payments = graphene.Field(
        'bank.schema.nodes.PaymentPaginatedNode', page=graphene.Int(), page_size=graphene.Int(), status=graphene.String())

    all_payment_methods = graphene.List(
        'bank.schema.nodes.PaymentMethodNode')

    my_payments = DjangoFilterConnectionField('bank.schema.nodes.PaymentNode')

    def resolve_payment(self, info, **kwargs):
        if not kwargs.get('id'):
            return None
        id = kwargs.get('id')
        global_id = from_global_id(id)[1]
        return Payment.objects.get(id=global_id)

    def resolve_all_payments(self, info, page, page_size=10, **kwargs):
        if not info.context.user.is_authenticated:
            raise GraphQLError(_('Unauthenticated.'))
        if not info.context.user.is_staff:
            raise GraphQLError(_('Unauthorized.'))

        qs = Payment.objects.all()
        qs = qs.filter(status=kwargs.get('status')
                       ) if kwargs.get('status') else qs

        if page_size == 0:
            page_size = Payment.objects.all().count()

        return get_paginator(qs, page_size, page, PaymentPaginatedNode)

    def resolve_all_payment_methods(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            raise GraphQLError(_('Unauthenticated.'))

        return PaymentMethod.objects.all()

    def resolve_my_payments(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            raise GraphQLError(_('Unauthenticated.'))

        return Payment.objects.filter(user=info.context.user)
