import graphene
from activities.models import Activity, Schedule
from activities.schema.nodes import SchedulePaginatedNode
from django.utils.translation import gettext as _
from graphql import GraphQLError
from graphql_relay import from_global_id
from utils.utils import get_paginator


class Query(graphene.ObjectType):
    schedule = graphene.Field(
        'activities.schema.nodes.ScheduleNode',   schedule_id=graphene.ID())
    all_activities = graphene.List('activities.schema.nodes.ActivityNode')

    def resolve_schedule(self, info, **kwargs):
        if not kwargs.get('schedule_id'):
            return None

        if not info.context.user.is_authenticated:
            raise GraphQLError(_('Unauthorized.'))
        if info.context.user.is_staff is False:
            raise GraphQLError(_('Unauthorized.'))

        id = from_global_id(kwargs.get('schedule_id'))[1]
        return Schedule.objects.get(id=id)

    def resolve_all_activities(self, info):
        return Activity.objects.filter(is_active=True)
