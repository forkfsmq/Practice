import uuid
from datetime import datetime, date, time
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone

from .models import (
    Workplace, MeetingRoom, Tariff, ExtraService,
    Booking, TimeSlot, Payment, DailyPass, CustomUser, BookingService
)
from .forms import BookingForm, CheckoutPaymentForm, SearchFilterForm


def index(request):
    """Home page view (Занятие 7, 8, 9)"""
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
    """Catalog & interactive floor map view (Занятие 8, 9)"""
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
    """
    Booking page with 14-hour slot picker, dynamic price & 20% discount calculator,
    and server-side collision prevention (Занятие 8 & 9)
    """
    resource_type = request.GET.get('type', request.POST.get('resource_type', 'workplace'))
    if resource_type == 'room':
        room = get_object_or_404(MeetingRoom, pk=resource_id)
        workplace = None
        resource_name = f'Переговорная «{room.name}»'
        hourly_rate = float(room.price_per_hour)
    else:
        workplace = get_object_or_404(Workplace, pk=resource_id)
        room = None
        resource_name = f'Рабочее место {workplace.number}'
        hourly_rate = float(workplace.price_per_hour)

    extra_services = ExtraService.objects.filter(is_active=True)
    form_errors = None

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            slot_date = form.cleaned_data['slot_date']
            hours = form.cleaned_data['selected_slots']
            guest_name = form.cleaned_data['guest_name']
            guest_phone = form.cleaned_data['guest_phone']
            guest_email = form.cleaned_data['guest_email']
            selected_services = form.cleaned_data.get('services', [])

            # Calculation
            count_hours = len(hours)
            base_sum = count_hours * hourly_rate
            discount = 0.0
            if count_hours >= 6:
                discount = round(base_sum * 0.20, 2)

            services_sum = sum(float(s.price) for s in selected_services)
            total_price = max(0.0, base_sum - discount + services_sum)

            # Find or get user
            user = CustomUser.objects.filter(email=guest_email).first()
            if not user:
                user = CustomUser.objects.filter(username='stas').first() or CustomUser.objects.first()

            # Find tariff
            tariff_type = 'daily' if count_hours >= 6 else 'hourly'
            tariff = Tariff.objects.filter(tariff_type=tariff_type).first() or Tariff.objects.first()

            # Start and End Datetime
            start_dt = timezone.make_aware(datetime.combine(slot_date, time(hour=hours[0], minute=0)))
            end_dt = timezone.make_aware(datetime.combine(slot_date, time(hour=hours[-1] + 1, minute=0)))

            # Create Booking
            booking = Booking.objects.create(
                user=user,
                workplace=workplace,
                meeting_room=room,
                tariff=tariff,
                start_datetime=start_dt,
                end_datetime=end_dt,
                total_price=total_price,
                status='pending'
            )

            # Create TimeSlots
            for h in hours:
                TimeSlot.objects.create(
                    booking=booking,
                    workplace=workplace,
                    meeting_room=room,
                    slot_date=slot_date,
                    start_hour=h,
                    end_hour=h + 1,
                    is_occupied=True
                )

            # Create BookingServices
            for srv in selected_services:
                BookingService.objects.create(
                    booking=booking,
                    service=srv,
                    quantity=1,
                    price_at_booking=srv.price,
                    total_amount=srv.price
                )

            # Create Initial Pending Payment
            Payment.objects.create(
                booking=booking,
                amount=total_price,
                payment_type='card',
                payment_method='online',
                status='pending',
                transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}"
            )

            messages.success(request, f'Бронирование #BK-{booking.id} успешно создано! Переходим к оплате.')
            return redirect('coworking:checkout', booking_id=booking.id)
        else:
            form_errors = form.errors
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме бронирования.')
    else:
        form = BookingForm(initial={
            'resource_id': resource_id,
            'resource_type': resource_type,
            'slot_date': date.today().strftime('%Y-%m-%d'),
            'selected_slots': '10,11,12,13,14,15,16,17',
            'guest_name': 'Станислав Перкакуев',
            'guest_phone': '+7 (999) 123-45-67',
            'guest_email': 'stas@coworkhub.ru',
        })

    context = {
        'resource_id': resource_id,
        'resource_type': resource_type,
        'workplace': workplace,
        'room': room,
        'resource_name': resource_name,
        'hourly_rate': hourly_rate,
        'extra_services': extra_services,
        'form': form,
        'form_errors': form_errors,
    }
    return render(request, 'coworking/booking.html', context)


def checkout(request, booking_id):
    """Checkout / Payment confirmation page (Занятие 8 & 9)"""
    booking = get_object_or_404(Booking, pk=booking_id)
    payment = booking.payments.first()

    if request.method == 'POST':
        form = CheckoutPaymentForm(request.POST)
        if form.is_valid():
            # Update payment
            if payment:
                payment.status = 'completed'
                payment.save()

            # Activate booking
            booking.status = 'active'
            booking.save()

            # Create or update DailyPass
            pass_code = f"PASS-2026-B{booking.id}-{uuid.uuid4().hex[:4].upper()}"
            daily_pass, _ = DailyPass.objects.get_or_create(
                booking=booking,
                defaults={
                    'pass_code': pass_code,
                    'valid_date': booking.start_datetime.date(),
                    'guest_name': form.cleaned_data['payer_name'],
                    'status': 'active',
                    'activated_at': timezone.now()
                }
            )

            messages.success(request, f'Оплата {booking.total_price:.0f} ₽ успешно подтверждена! Ваш пропуск активен.')
            return redirect('coworking:dailypass_detail', pass_code=daily_pass.pass_code)
        else:
            messages.error(request, 'Пожалуйста, проверьте данные оплаты.')
    else:
        form = CheckoutPaymentForm(initial={
            'payment_method': 'card_mir',
            'payer_name': booking.user.get_full_name() or 'Станислав Перкакуев',
            'payer_email': booking.user.email or 'stas@coworkhub.ru',
            'agree_terms': True
        })

    context = {
        'booking': booking,
        'payment': payment,
        'form': form,
    }
    return render(request, 'coworking/checkout.html', context)


def profile(request):
    """Resident personal cabinet / Profile view (Занятие 8 & 9)"""
    user = CustomUser.objects.filter(username='stas').first() or CustomUser.objects.first()

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
    """Search results view with filters and pagination (Занятие 8, 9)"""
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
    end_dt = booking.end_datetime
    new_end_dt = end_dt + timezone.timedelta(hours=1)
    local_new_end = timezone.localtime(new_end_dt)
    target_start_hour = local_new_end.hour - 1
    target_date = local_new_end.date()
    extension_price = 350.00

    # Overbooking / collision check
    if booking.workplace:
        collision = TimeSlot.objects.filter(
            workplace=booking.workplace,
            slot_date=target_date,
            start_hour=target_start_hour,
            is_occupied=True
        ).exclude(booking=booking).exists()

        if collision:
            return JsonResponse({
                'success': False,
                'error': f'Слот {target_start_hour}:00–{local_new_end.hour}:00 уже забронирован другим резидентом!'
            }, status=409)

    booking.end_datetime = new_end_dt
    booking.total_price = float(booking.total_price) + extension_price
    booking.is_extended = True
    booking.save()

    # Record or update slot
    if booking.workplace:
        TimeSlot.objects.get_or_create(
            workplace=booking.workplace,
            slot_date=target_date,
            start_hour=target_start_hour,
            defaults={
                'booking': booking,
                'end_hour': local_new_end.hour,
                'is_occupied': True
            }
        )

    return JsonResponse({
        'success': True,
        'message': 'Бронирование успешно продлено на 1 час (+350 ₽)!',
        'new_end_time': local_new_end.strftime('%H:%M'),
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
