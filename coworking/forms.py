import re
from datetime import date
from django import forms
from django.core.exceptions import ValidationError
from .models import Workplace, MeetingRoom, ExtraService, TimeSlot, Booking, Payment, Tariff, CustomUser

class BookingForm(forms.Form):
    """
    Форма создания бронирования рабочего места или переговорной комнаты
    с серверной валидацией, защитой от коллизий и автоматическим расчетом стоимости
    """
    resource_id = forms.IntegerField(widget=forms.HiddenInput())
    resource_type = forms.ChoiceField(
        choices=[('workplace', 'Рабочее место'), ('room', 'Переговорная комната')],
        widget=forms.HiddenInput()
    )
    slot_date = forms.DateField(
        label='Дата бронирования',
        input_formats=['%Y-%m-%d', '%d.%m.%Y'],
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    selected_slots = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
        error_messages={'required': 'Необходимо выбрать хотя бы один доступный слот времени.'}
    )
    guest_name = forms.CharField(
        label='ФИО гостя или резидента',
        min_length=3,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов Иван Иванович'})
    )
    guest_phone = forms.CharField(
        label='Номер телефона',
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'})
    )
    guest_email = forms.EmailField(
        label='Электронная почта',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    services = forms.ModelMultipleChoiceField(
        queryset=ExtraService.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    def clean_guest_phone(self):
        phone = self.cleaned_data.get('guest_phone', '').strip()
        cleaned_digits = re.sub(r'\D', '', phone)
        if len(cleaned_digits) < 10 or len(cleaned_digits) > 11:
            raise ValidationError('Введите корректный номер телефона (не менее 10 цифр).')
        return phone

    def clean_selected_slots(self):
        raw_slots = self.cleaned_data.get('selected_slots', '').strip()
        if not raw_slots:
            raise ValidationError('Выберите хотя бы один слот времени.')
        try:
            hours = [int(h) for h in raw_slots.split(',') if h.strip()]
        except ValueError:
            raise ValidationError('Некорректный формат выбранных часов.')

        if not hours:
            raise ValidationError('Выберите хотя бы один слот времени.')

        for h in hours:
            if h < 8 or h > 21:
                raise ValidationError('Время работы коворкинга строго с 08:00 до 22:00.')

        return sorted(hours)

    def clean(self):
        cleaned_data = super().clean()
        slot_date = cleaned_data.get('slot_date')
        resource_id = cleaned_data.get('resource_id')
        resource_type = cleaned_data.get('resource_type')
        hours = cleaned_data.get('selected_slots')

        if not (slot_date and resource_id and hours):
            return cleaned_data

        # Защита от бронирования в прошлом
        if slot_date < date.today():
            raise ValidationError('Невозможно забронировать слот в прошедшей дате.')

        # Строгая проверка на пересечение броней (защита от овербукинга)
        if resource_type == 'room':
            conflicts = TimeSlot.objects.filter(
                meeting_room_id=resource_id,
                slot_date=slot_date,
                start_hour__in=hours,
                is_occupied=True
            )
        else:
            conflicts = TimeSlot.objects.filter(
                workplace_id=resource_id,
                slot_date=slot_date,
                start_hour__in=hours,
                is_occupied=True
            )

        if conflicts.exists():
            conflict_hours = [f"{c.start_hour}:00–{c.end_hour}:00" for c in conflicts]
            raise ValidationError(
                f"Выбранные часы ({', '.join(conflict_hours)}) уже заняты другим пользователем. "
                "Пожалуйста, выберите другие доступные слоты."
            )

        return cleaned_data


class CheckoutPaymentForm(forms.Form):
    """
    Форма подтверждения оплаты бронирования
    """
    payment_method = forms.ChoiceField(
        choices=[
            ('card_mir', 'Банковская карта МИР / Visa / Mastercard'),
            ('sbp', 'Система быстрых платежей (СБП)'),
            ('balance', 'С баланса резидента'),
        ],
        initial='card_mir',
        widget=forms.RadioSelect()
    )
    payer_name = forms.CharField(
        label='Плательщик',
        min_length=3,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    payer_email = forms.EmailField(
        label='Электронная почта',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    agree_terms = forms.BooleanField(
        required=True,
        error_messages={'required': 'Вы должны согласиться с правилами коворкинга.'}
    )


class SearchFilterForm(forms.Form):
    """
    Форма поиска свободных рабочих мест
    """
    zone = forms.ChoiceField(
        choices=[
            ('', 'Все зоны коворкинга'),
            ('open_space', 'Open Space (Этаж 1)'),
            ('quiet_zone', 'Тихая зона (Этаж 2)'),
            ('window_view', 'Места у окна (Этаж 1-2)'),
            ('meeting', 'Переговорные комнаты'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    hours = forms.IntegerField(
        required=False,
        initial=8,
        widget=forms.Select(
            choices=[
                (1, '1 час (пробный)'),
                (4, '4 часа (полдня)'),
                (8, '8 часов (день со скидкой -20%)'),
                (12, '12 часов (полный день)'),
            ],
            attrs={'class': 'form-select'}
        )
    )
