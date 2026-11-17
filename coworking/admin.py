# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Workplace, MeetingRoom, Tariff,
    ExtraService, Booking, BookingService, TimeSlot,
    Payment, DailyPass
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'last_name', 'first_name', 'role', 'phone', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Данные коворкинга', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Данные коворкинга', {'fields': ('role', 'phone')}),
    )


@admin.register(Workplace)
class WorkplaceAdmin(admin.ModelAdmin):
    list_display = ['number', 'zone', 'floor', 'has_monitor', 'has_sockets', 'price_per_hour', 'is_active']
    list_filter = ['zone', 'floor', 'has_monitor', 'is_active']
    search_fields = ['number', 'description']


@admin.register(MeetingRoom)
class MeetingRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'floor', 'price_per_hour', 'is_active']
    list_filter = ['floor', 'is_active']
    search_fields = ['name', 'equipment']


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ['name', 'tariff_type', 'target_type', 'price', 'duration_hours', 'is_active']
    list_filter = ['tariff_type', 'target_type', 'is_active']


@admin.register(ExtraService)
class ExtraServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'unit', 'is_active']
    list_filter = ['is_active']


class BookingServiceInline(admin.TabularInline):
    model = BookingService
    extra = 1


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'get_resource', 'tariff', 'start_datetime', 'end_datetime', 'total_price', 'status', 'is_extended']
    list_filter = ['status', 'is_extended', 'tariff__tariff_type']
    search_fields = ['user__username', 'workplace__number', 'meeting_room__name']
    inlines = [BookingServiceInline]

    def get_resource(self, obj):
        return obj.workplace.number if obj.workplace else (obj.meeting_room.name if obj.meeting_room else "—")
    get_resource.short_description = "Объект брони"


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['id', 'slot_date', 'start_hour', 'end_hour', 'get_resource', 'is_occupied', 'booking']
    list_filter = ['slot_date', 'is_occupied']
    search_fields = ['workplace__number', 'meeting_room__name']

    def get_resource(self, obj):
        return obj.workplace.number if obj.workplace else (obj.meeting_room.name if obj.meeting_room else "—")
    get_resource.short_description = "Ресурс"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'booking', 'amount', 'payment_type', 'payment_method', 'status', 'payment_date']
    list_filter = ['payment_type', 'payment_method', 'status']
    search_fields = ['transaction_id', 'booking__id']


@admin.register(DailyPass)
class DailyPassAdmin(admin.ModelAdmin):
    list_display = ['pass_code', 'guest_name', 'valid_date', 'status', 'activated_at', 'booking']
    list_filter = ['status', 'valid_date']
    search_fields = ['pass_code', 'guest_name']
