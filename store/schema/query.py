import graphene
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from graphql import GraphQLError
from store.models import Cart, Item
from store.schema.nodes import CartPaginatedNode, ItemPaginatedNode
from utils.utils import get_paginator


class Query(graphene.ObjectType):
    digital_items = graphene.Field(
        'store.schema.nodes.ItemPaginatedNode', page=graphene.Int())
    analog_items = graphene.Field(
        'store.schema.nodes.ItemPaginatedNode', page=graphene.Int())

    cart = graphene.Field('store.schema.nodes.CartNode',
                          user_username=graphene.String())

    all_carts = graphene.List(
        'store.schema.nodes.CartNode')

    def resolve_analog_items(self, info, page=1):
        page_size = 10
        qs = Item.objects.filter(
            is_analog=True, is_active=True, is_variation=False)

        return get_paginator(qs, page_size, page, ItemPaginatedNode)

    def resolve_digital_items(self, info, page=1):
        page_size = 10
        qs = Item.objects.filter(
            is_digital=True, is_active=True, is_variation=False)

        return get_paginator(qs, page_size, page, ItemPaginatedNode)

    def resolve_cart(self, info, user_username=None):
        user = info.context.user
        if not user.is_authenticated:
            return None
        if user.is_staff and user_username is not None:
            user = User.objects.filter(username=user_username).first()
        return user.carts.filter(checked_out=False).first()

    def resolve_all_carts(self, info, *args, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            return GraphQLError(_('Unauthenticated.'))

        if not user.is_staff:
            return GraphQLError(_('Unauthorized.'))

        return Cart.objects.all()
