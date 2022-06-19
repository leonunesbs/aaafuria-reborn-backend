import graphene
from graphene_django import DjangoObjectType
from graphql_relay import to_global_id
from store.models import Cart, CartItem, Item


class ItemNode(DjangoObjectType):
    method = graphene.String()

    class Meta:
        model = Item
        interfaces = (graphene.relay.Node, )
        filter_fields = []

    def resolve_image(self, info, *args, **kwargs):
        return info.context.build_absolute_uri(self.image.url)


class ItemPaginatedNode(graphene.ObjectType):
    page = graphene.Int()
    pages = graphene.Int()
    has_next = graphene.Boolean()
    has_prev = graphene.Boolean()
    objects = graphene.List(ItemNode)


class CartItemNode(DjangoObjectType):
    class Meta:
        model = CartItem
        interfaces = (graphene.relay.Node, )
        filter_fields = []


class CartNode(DjangoObjectType):
    total = graphene.Float(source='get_total')
    disabled_payment_methods = graphene.List(graphene.ID)

    class Meta:
        model = Cart
        interfaces = (graphene.relay.Node, )
        filter_fields = ['ordered', 'delivered']

    def resolve_disabled_payment_methods(self, info, *args, **kwargs):
        disabled_payment_methods = set()
        for cart_item in self.items.all():
            for payment_method in cart_item.item.disabled_payment_methods.all():
                disabled_payment_methods.add(payment_method.title)
        return list(disabled_payment_methods)


class CartPaginatedNode(graphene.ObjectType):
    page = graphene.Int()
    pages = graphene.Int()
    has_next = graphene.Boolean()
    has_prev = graphene.Boolean()
    objects = graphene.List(CartNode)
