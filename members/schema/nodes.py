import graphene
from django.conf import settings
from graphene_django import DjangoObjectType
from members.models import Member

API_KEY = settings.STRIPE_API_KEY


class MemberNode(DjangoObjectType):
    first_teamer = graphene.Boolean(source='first_teamer')
    has_active_membership = graphene.Boolean(source='has_active_membership')
    active_membership = graphene.Field(
        'memberships.schema.nodes.MembershipNode')
    billing_portal_url = graphene.String()
    whatsapp_url = graphene.String()

    class Meta:
        model = Member
        interfaces = (graphene.relay.Node,)
        filter_fields = []

    def resolve_billing_portal_url(self, info, *args, **kwargs):
        import stripe
        stripe.api_key = API_KEY
        session = stripe.billing_portal.Session.create(
            customer=self.attachments.get(title="stripe_customer_id").content,
            return_url="https://aaafuria.site",
            locale='pt-BR',
        )
        return session.url

    def resolve_avatar(self, info, *args, **kwargs):
        if self.avatar:
            return info.context.build_absolute_uri(self.avatar.url)

    def resolve_whatsapp_url(self, info, *args, **kwargs):
        return f'https://wa.me/55{self.phone}'
