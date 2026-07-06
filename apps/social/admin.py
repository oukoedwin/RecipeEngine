from django.contrib import admin
from .models import DinnerEvent, EventDish, EventInvite


@admin.register(DinnerEvent)
class DinnerEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'date', 'time', 'location')
    search_fields = ('title', 'host__username')


@admin.register(EventDish)
class EventDishAdmin(admin.ModelAdmin):
    list_display = ('event', 'recipe', 'claimed_by')


@admin.register(EventInvite)
class EventInviteAdmin(admin.ModelAdmin):
    list_display = ('event', 'recipient', 'status', 'responded_at')
    list_filter = ('status',)
    search_fields = ('event__title', 'recipient__username')
