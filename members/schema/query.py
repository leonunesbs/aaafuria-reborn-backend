import graphene
from django.utils.translation import gettext as _
from graphql import GraphQLError
from members.models import Member


class Query(graphene.ObjectType):
    all_members = graphene.List('members.schema.nodes.MemberNode')

    member_by_registration = graphene.Field(
        'members.schema.nodes.MemberNode', registration=graphene.String())
    check_member = graphene.Boolean(
        registration=graphene.String())

    def resolve_all_members(self, info, *args, **kwargs):
        if not info.context.user.is_authenticated:
            return GraphQLError(_('Unauthenticated.'))
        if not info.context.user.is_staff:
            return GraphQLError(_('Unauthorized.'))

        return Member.objects.all()

    def resolve_member_by_registration(self, info,  **kwargs):
        if not info.context.user.is_authenticated:
            return GraphQLError(_('Unauthenticated.'))
        if not info.context.user.is_staff:
            return GraphQLError(_('Unauthorized.'))

        registration = kwargs.get('registration')

        if not registration:
            return None

        return Member.objects.get(registration=registration)

    def resolve_check_member(self, info, **kwargs):
        registration = kwargs.get('registration')
        if not registration:
            return False
        return Member.objects.filter(registration=registration).exists()
