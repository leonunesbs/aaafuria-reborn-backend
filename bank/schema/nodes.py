import graphene
from bank.models import Attachment, Payment, PaymentMethod
from graphene_django import DjangoObjectType
from graphql_relay import to_global_id


class PaymentMethodNode(DjangoObjectType):
    class Meta:
        model = PaymentMethod
        interfaces = (graphene.relay.Node,)
        filter_fields = []


class PaymentNode(DjangoObjectType):
    method = graphene.String()

    class Meta:
        model = Payment
        interfaces = (graphene.relay.Node, )
        filter_fields = ['status']

    def resolve_method(self, info):
        return self.method.name


class PaymentPaginatedNode(graphene.ObjectType):
    page = graphene.Int()
    pages = graphene.Int()
    has_next = graphene.Boolean()
    has_prev = graphene.Boolean()
    objects = graphene.List(PaymentNode)


class AttachmentNode(DjangoObjectType):
    class Meta:
        model = Attachment
        interfaces = (graphene.relay.Node, )
        filter_fields = []

    def resolve_file(self, info, *args, **kwargs):
        return info.context.build_absolute_uri(self.file.url)
