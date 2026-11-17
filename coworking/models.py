# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models import Q, F, CheckConstraint, UniqueConstraint
from decimal import Decimal


class CustomUser(AbstractUser):
    """
    Пользователь информационной системы коворкинга с ролевой моделью.
    Роли: гость, резидент, администратор, бухгалтер.
    """
    ROLE_CHOICES = [
        ('guest', 'Гость'),
        ('resident', 'Резидент'),
        ('admin', 'Администратор'),
        ('accountant', 'Бухгалтер'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='resident',
        verbose_name='Роль в системе'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Номер телефона'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата регистрации'
    )

    class Meta:
        verbose_name = 'Пользователь коворкинга'
        verbose_name_plural = 'Пользователи коворкинга'
        ordering = ['-date_joined']

    def __str__(self):
        full = f"{self.last_name} {self.first_name}".strip()
        role_label = self.get_role_display()
        return f"{full or self.username} ({role_label})"


class Workplace(models.Model):
    """
    Рабочее место в коворкинге (опенспейс, тихая зона, у окна).
    """
    ZONE_CHOICES = [
        ('open_space', 'Опенспейс общая зона'),
        ('quiet_zone', 'Тихая зона концентрации'),
        ('window_view', 'Зона у панорамных окон'),
    ]

    number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Номер места (код стола)'
    )
    zone = models.CharField(
        max_length=30,
        choices=ZONE_CHOICES,
        default='open_space',
        verbose_name='Зона размещения'
    )
    floor = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Этаж'
    )
    has_monitor = models.BooleanField(
        default=False,
        verbose_name='Второй монитор (27 дюймов)'
    )
    has_sockets = models.BooleanField(
        default=True,
        verbose_name='Блок розеток и USB-порты'
    )
    price_per_hour = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Базовая ставка в час (руб.)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Доступно для бронирования'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Примечание / Описание'
    )

    class Meta:
        verbose_name = 'Рабочее место'
        verbose_name_plural = 'Рабочие места'
        ordering = ['zone', 'number']

    def __str__(self):
        return f"Стол {self.number} ({self.get_zone_display()})"


class MeetingRoom(models.Model):
    """
    Переговорная комната коворкинга.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название переговорной'
    )
    capacity = models.PositiveSmallIntegerField(
        verbose_name='Вместимость (человек)'
    )
    floor = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Этаж'
    )
    equipment = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Оборудование (проектор, ТВ, маркерная доска)'
    )
    price_per_hour = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Базовая ставка в час (руб.)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Доступна для аренды'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Подробное описание'
    )

    class Meta:
        verbose_name = 'Переговорная комната'
        verbose_name_plural = 'Переговорные комнаты'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (до {self.capacity} чел.)"


class Tariff(models.Model):
    """
    Тарифная сетка: почасовой, дневной (от 8 ч) и месячный абонемент.
    """
    TARIFF_TYPE_CHOICES = [
        ('hourly', 'Почасовой'),
        ('daily', 'Дневной пропуск'),
        ('monthly', 'Месячное резидентство'),
    ]
    TARGET_TYPE_CHOICES = [
        ('workplace', 'Рабочее место'),
        ('meeting_room', 'Переговорная комната'),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name='Наименование тарифа'
    )
    tariff_type = models.CharField(
        max_length=20,
        choices=TARIFF_TYPE_CHOICES,
        default='hourly',
        verbose_name='Периодичность тарифа'
    )
    target_type = models.CharField(
        max_length=20,
        choices=TARGET_TYPE_CHOICES,
        default='workplace',
        verbose_name='Применяется к объекту'
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Фиксированная стоимость (руб.)'
    )
    duration_hours = models.PositiveIntegerField(
        default=1,
        verbose_name='Включено часов в тариф'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Тариф действует'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Условия тарифа'
    )

    class Meta:
        verbose_name = 'Тарифный план'
        verbose_name_plural = 'Тарифные планы'
        ordering = ['target_type', 'price']

    def __str__(self):
        return f"{self.name} — {self.price} руб. ({self.get_tariff_type_display()})"


class ExtraService(models.Model):
    """
    Дополнительные услуги: кофе, печать документов, аренда флипчарта, локер.
    """
    name = models.CharField(
        max_length=120,
        verbose_name='Наименование услуги'
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Стоимость за единицу (руб.)'
    )
    unit = models.CharField(
        max_length=30,
        default='шт.',
        verbose_name='Единица измерения'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Доступна для заказа'
    )

    class Meta:
        verbose_name = 'Дополнительная услуга'
        verbose_name_plural = 'Дополнительные услуги'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.price} руб. / {self.unit})"


class Booking(models.Model):
    """
    Бронирование рабочего места или переговорной резидентом.
    """
    STATUS_CHOICES = [
        ('new', 'Новое (ожидает оплаты)'),
        ('confirmed', 'Подтверждено'),
        ('paid', 'Оплачено'),
        ('active', 'Действует (клиент в коворкинге)'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Клиент / Резидент'
    )
    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
        verbose_name='Рабочее место'
    )
    meeting_room = models.ForeignKey(
        MeetingRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
        verbose_name='Переговорная комната'
    )
    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name='Примененный тариф'
    )
    services = models.ManyToManyField(
        ExtraService,
        through='BookingService',
        related_name='bookings',
        blank=True,
        verbose_name='Заказанные доп. услуги'
    )
    start_datetime = models.DateTimeField(
        verbose_name='Дата и время начала'
    )
    end_datetime = models.DateTimeField(
        verbose_name='Дата и время окончания'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Итоговая сумма (руб.)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Статус бронирования'
    )
    is_extended = models.BooleanField(
        default=False,
        verbose_name='Было продлено'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата оформления'
    )

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-start_datetime']
        constraints = [
            # Проверка 1: должно быть заполнено либо рабочее место, либо переговорная комната
            CheckConstraint(
                condition=(
                    (Q(workplace__isnull=False) & Q(meeting_room__isnull=True)) |
                    (Q(workplace__isnull=True) & Q(meeting_room__isnull=False))
                ),
                name='chk_booking_single_resource_type'
            ),
            # Проверка 2: время окончания должно быть строго позже времени начала
            CheckConstraint(
                condition=Q(end_datetime__gt=F('start_datetime')),
                name='chk_booking_valid_interval'
            ),
        ]

    def clean(self):
        super().clean()
        if not self.workplace and not self.meeting_room:
            raise ValidationError("Необходимо выбрать либо стол, либо переговорную!")
        if self.workplace and self.meeting_room:
            raise ValidationError("Нельзя одновременно выбрать и стол, и переговорную комнату!")
        if self.start_datetime and self.end_datetime and self.end_datetime <= self.start_datetime:
            raise ValidationError("Время окончания должно быть позже времени начала бронирования!")

    def __str__(self):
        res = self.workplace.number if self.workplace else self.meeting_room.name
        return f"Бронь №{self.pk or 'новая'} — {res} ({self.user.username}) — {self.get_status_display()}"


class BookingService(models.Model):
    """
    Связующая модель для связи многие-ко-многим между бронированием и услугами (through-модель).
    Хранит количество заказанных услуг и цену на момент фиксации брони.
    """
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='booking_services',
        verbose_name='Бронирование'
    )
    service = models.ForeignKey(
        ExtraService,
        on_delete=models.PROTECT,
        related_name='service_orders',
        verbose_name='Услуга'
    )
    quantity = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Количество'
    )
    price_at_booking = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Цена за ед. при заказе (руб.)'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Общая стоимость по позиции (руб.)'
    )

    class Meta:
        verbose_name = 'Услуга в бронировании'
        verbose_name_plural = 'Услуги в бронированиях'
        ordering = ['booking', 'service']
        constraints = [
            UniqueConstraint(
                fields=['booking', 'service'],
                name='unique_service_per_booking'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.price_at_booking:
            self.price_at_booking = self.service.price
        self.total_amount = self.price_at_booking * Decimal(self.quantity)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service.name} x {self.quantity} в брони №{self.booking.pk}"


class TimeSlot(models.Model):
    """
    Почасовой слот времени для отображения сетки занятости и защиты от коллизий (овербукинга).
    """
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='time_slots',
        null=True,
        blank=True,
        verbose_name='Связанное бронирование'
    )
    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='time_slots',
        verbose_name='Рабочее место'
    )
    meeting_room = models.ForeignKey(
        MeetingRoom,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='time_slots',
        verbose_name='Переговорная комната'
    )
    slot_date = models.DateField(
        verbose_name='Дата слота'
    )
    start_hour = models.PositiveSmallIntegerField(
        verbose_name='Час начала (0-23)'
    )
    end_hour = models.PositiveSmallIntegerField(
        verbose_name='Час окончания (1-24)'
    )
    is_occupied = models.BooleanField(
        default=True,
        verbose_name='Слот занят'
    )

    class Meta:
        verbose_name = 'Слот времени'
        verbose_name_plural = 'Сетка слотов времени'
        ordering = ['slot_date', 'start_hour']
        constraints = [
            # Проверка корректности интервала часов
            CheckConstraint(
                condition=Q(start_hour__lt=F('end_hour')) & Q(end_hour__lte=24),
                name='chk_timeslot_valid_hour_range'
            ),
            # Защита от овербукинга стола: один стол в одну дату на один час нельзя занять дважды
            UniqueConstraint(
                fields=['workplace', 'slot_date', 'start_hour'],
                condition=Q(workplace__isnull=False),
                name='unique_workplace_slot_per_hour'
            ),
            # Защита от овербукинга переговорной: одна комната в одну дату на один час не может быть занята дважды
            UniqueConstraint(
                fields=['meeting_room', 'slot_date', 'start_hour'],
                condition=Q(meeting_room__isnull=False),
                name='unique_meetingroom_slot_per_hour'
            ),
        ]

    def __str__(self):
        res = self.workplace.number if self.workplace else (self.meeting_room.name if self.meeting_room else "—")
        return f"{res} | {self.slot_date} {self.start_hour:02d}:00-{self.end_hour:02d}:00"


class Payment(models.Model):
    """
    Платеж за бронирование или продление аренды.
    """
    PAYMENT_TYPE_CHOICES = [
        ('primary', 'Первичная оплата брони'),
        ('extension', 'Доплата за продление слота'),
        ('refund', 'Возврат денежных средств'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Банковская карта (онлайн)'),
        ('invoice', 'Безналичный расчет для юрлиц'),
        ('cash', 'Наличные администратору на стойке'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Ожидает проведения'),
        ('completed', 'Успешно оплачено'),
        ('failed', 'Отклонено банком'),
        ('refunded', 'Средства возвращены'),
    ]

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Оплачиваемое бронирование'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма транзакции (руб.)'
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='primary',
        verbose_name='Тип платежа'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='card',
        verbose_name='Способ оплаты'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        verbose_name='Статус платежа'
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Идентификатор чека / транзакции'
    )
    payment_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время оплаты'
    )

    class Meta:
        verbose_name = 'Оплата'
        verbose_name_plural = 'Платежи и транзакции'
        ordering = ['-payment_date']

    def __str__(self):
        return f"Чек {self.transaction_id} — {self.amount} руб. ({self.get_status_display()})"


class DailyPass(models.Model):
    """
    Электронный дневной пропуск с QR-кодом для посещения коворкинга.
    """
    STATUS_CHOICES = [
        ('active', 'Действителен'),
        ('used', 'Использован на турникете'),
        ('expired', 'Истек срок действия'),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='daily_pass',
        verbose_name='Связанное бронирование'
    )
    pass_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Уникальный номер пропуска'
    )
    valid_date = models.DateField(
        verbose_name='Дата действия пропуска'
    )
    guest_name = models.CharField(
        max_length=150,
        verbose_name='ФИО посетителя'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Статус пропуска'
    )
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время прохода / активации'
    )

    class Meta:
        verbose_name = 'Дневной пропуск'
        verbose_name_plural = 'Дневные пропуска'
        ordering = ['-valid_date', 'pass_code']

    def __str__(self):
        return f"Пропуск {self.pass_code} ({self.guest_name}) на {self.valid_date}"
