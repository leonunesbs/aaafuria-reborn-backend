from django.contrib import admin

from memberships.models import Attachment, Membership, MembershipPlan


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('member', 'membership_plan', 'is_active')
    search_fields = ('member__email', 'member__name',
                     'member__registration', 'ref_id')
    list_filter = ('is_active', 'membership_plan')


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    pass


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'content', 'membership')
    search_fields = ('membership__member__email',
                     'membership__member__name', 'membership__member__registration', 'title', 'content')
