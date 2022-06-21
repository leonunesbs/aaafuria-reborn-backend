from django.contrib import admin

from activities.models import Activity, Attachment, Category, Schedule


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active']
    filter_horizontal = ['first_team']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['activity', 'description', 'status', 'start_date', 'end_date',
                    'location', 'cost', 'max_participants', 'min_participants', 'is_active']
    filter_horizontal = ['users_confirmed', 'users_present']


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['schedule', 'title']
