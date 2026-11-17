from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from .models import Workplace, MeetingRoom, Tariff, ExtraService, Booking, TimeSlot, Payment, DailyPass, CustomUser

def index(request):
    """Home page view (Занятие 7 & 8)"""
    tariffs = Tariff.objects.filter(is_active=True).order_by('price')
    popular_workplaces = Workplace.objects.filter(is_active=True).order_by('floor', 'number')[:4]
    meeting_rooms = MeetingRoom.objects.filter(is_active=True).order_by('id')[:3]

    context = {
        'tariffs': tariffs,
        'popular_workplaces': popular_workplaces,
        'meeting_rooms': meeting_rooms,
    }
    return render(request, 'coworking/index.html', context)

def catalog(request):
    """Catalog & interactive floor map view (Занятие 8)"""
    zone_filter = request.GET.get('zone', '')
    floor_filter = request.GET.get('floor', '')

    workplaces = Workplace.objects.filter(is_active=True)
    if zone_filter:
        workplaces = workplaces.filter(zone=zone_filter)
    if floor_filter:
        workplaces = workplaces.filter(floor=floor_filter)

    meeting_rooms = MeetingRoom.objects.filter(is_active=True)
    if floor_filter:
        meeting_rooms = meeting_rooms.filter(floor=floor_filter)

    context = {
        'workplaces': workplaces,
        'meeting_rooms': meeting_rooms,
        'zone_filter': zone_filter,
        'floor_filter': floor_filter,
    }
    return render(request, 'coworking/catalog.html', context)

def booking_detail(request, resource_id):
    """Booking page with 14-hour slot picker (Занятие 8 & 9)"""
    resource_type = request.GET.get('type', 'workplace')
    if resource_type == 'room':
        room = get_object_or_404(MeetingRoom, pk=resource_id)
        workplace = None
        resource_name = f'Переговорная «{room.name}»'
        hourly_rate = room.price_per_hour
    else:
        workplace = get_object_or_404(Workplace, pk=resource_id)
        room = None
        resource_name = f'Рабочее место {workplace.number}'
        hourly_rate = workplace.price_per_hour

    extra_services = ExtraService.objects.filter(is_active=True)
    context = {
        'resource_id': resource_id,
        'resource_type': resource_type,
        'workplace': workplace,
        'room': room,
        'resource_name': resource_name,
        'hourly_rate': hourly_rate,
        'extra_services': extra_services,
    }
    return render(request, 'coworking/booking.html', context)

def checkout(request, booking_id):
    """Checkout / Payment confirmation page (Занятие 8 & 9)"""
    booking = get_object_or_404(Booking, pk=booking_id)
    payment = booking.payments.first()
    context = {
        'booking': booking,
        'payment': payment,
    }
    return render(request, 'coworking/checkout.html', context)

def profile(request):
    """Resident personal cabinet / Profile view (Занятие 8 & 9)"""
    user = CustomUser.objects.filter(username='stas').first()
    if not user:
        user = CustomUser.objects.first()

    active_booking = Booking.objects.filter(status='active').order_by('-start_datetime').first()
    booking_history_list = Booking.objects.all().order_by('-created_at')

    # Requirement from Assignment 8: Paginator with 20 items per page
    paginator = Paginator(booking_history_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'resident': user,
        'active_booking': active_booking,
        'page_obj': page_obj,
    }
    return render(request, 'coworking/profile.html', context)

def dailypass_current(request):
    """Digital daily pass for active booking or latest pass"""
    pass_obj = DailyPass.objects.order_by('-id').first()
    if not pass_obj:
        return redirect('coworking:catalog')
    return redirect('coworking:dailypass_detail', pass_code=pass_obj.pass_code)

def dailypass_detail(request, pass_code):
    """Digital daily pass detail view (Занятие 8)"""
    pass_obj = get_object_or_404(DailyPass, pass_code=pass_code)
    context = {
        'pass_obj': pass_obj,
        'booking': pass_obj.booking,
    }
    return render(request, 'coworking/dailypass.html', context)

def rules(request):
    """Static coworking rules, tariffs & FAQ view (Занятие 8)"""
    tariffs = Tariff.objects.filter(is_active=True).order_by('price')
    return render(request, 'coworking/rules.html', {'tariffs': tariffs})

def search(request):
    """Search results view with filters and pagination (Занятие 8)"""
    zone = request.GET.get('zone', '')
    date_str = request.GET.get('date', '')
    hours = request.GET.get('hours', '8')

    results = Workplace.objects.filter(is_active=True)
    if zone and zone != 'meeting':
        results = results.filter(zone=zone)

    paginator = Paginator(results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'zone': zone,
        'date': date_str,
        'hours': hours,
    }
    return render(request, 'coworking/search_results.html', context)

def api_extend_booking(request, booking_id):
    """Custom JSON API endpoint: 1-hour booking extension with overbooking check (Занятие 9)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST-запросы разрешены'}, status=405)

    booking = get_object_or_404(Booking, pk=booking_id)
    # Check if already extended or expired
    end_dt = booking.end_datetime
    new_end_dt = end_dt + timezone.timedelta(hours=1)
    extension_price = 350.00

    # Overbooking / collision check
    if booking.workplace:
        target_hour = new_end_dt.hour
        collision = TimeSlot.objects.filter(
            workplace=booking.workplace,
            slot_date=new_end_dt.date(),
            start_hour=target_hour - 1,
            is_occupied=True
        ).exclude(booking=booking).exists()

        if collision:
            return JsonResponse({
                'success': False,
                'error': f'Слот {target_hour - 1}:00–{target_hour}:00 уже забронирован другим резидентом!'
            }, status=409)

    booking.end_datetime = new_end_dt
    booking.total_price += extension_price
    booking.is_extended = True
    booking.save()

    # Record or update slot
    if booking.workplace:
        TimeSlot.objects.create(
            booking=booking,
            workplace=booking.workplace,
            slot_date=new_end_dt.date(),
            start_hour=new_end_dt.hour - 1,
            end_hour=new_end_dt.hour,
            is_occupied=True
        )

    return JsonResponse({
        'success': True,
        'message': 'Бронирование успешно продлено на 1 час (+350 ₽)!',
        'new_end_time': booking.end_datetime.strftime('%H:%M'),
        'new_total_price': float(booking.total_price),
        'remaining_minutes': 102
    })

def api_get_slots(request, resource_id):
    """Custom JSON API endpoint to fetch booked slots for a resource on a given date"""
    date_str = request.GET.get('date', '2026-11-18')
    resource_type = request.GET.get('type', 'workplace')

    if resource_type == 'room':
        slots = TimeSlot.objects.filter(meeting_room_id=resource_id, slot_date=date_str, is_occupied=True)
    else:
        slots = TimeSlot.objects.filter(workplace_id=resource_id, slot_date=date_str, is_occupied=True)

    occupied_hours = list(slots.values_list('start_hour', flat=True))
    return JsonResponse({
        'date': date_str,
        'occupied_hours': occupied_hours
    })
