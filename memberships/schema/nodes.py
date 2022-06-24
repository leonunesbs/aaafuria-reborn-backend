import graphene
from graphene_django import DjangoObjectType
from memberships.models import Membership, MembershipPlan


class MembershipNode(DjangoObjectType):
    class Meta:
        model = Membership
        interfaces = (graphene.relay.Node, )
        filter_fields = ['is_active']


class MembershipPlanNode(DjangoObjectType):
    members_count = graphene.Int()

    class Meta:
        model = MembershipPlan
        interfaces = (graphene.relay.Node, )
        filter_fields = []

    def resolve_members_count(self, info):
        return Membership.objects.filter(membership_plan=self, is_active=True).count()
