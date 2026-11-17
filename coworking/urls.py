from django.urls import path
from . import views

app_name = 'coworking'

urlpatterns = [
    # Main pages (Assignment 7 & 8)
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('booking/<int:resource_id>/', views.booking_detail, name='booking_detail'),
    path('checkout/<int:booking_id>/', views.checkout, name='checkout'),
    path('profile/', views.profile, name='profile'),
    path('pass/', views.dailypass_current, name='dailypass'),
    path('pass/<str:pass_code>/', views.dailypass_detail, name='dailypass_detail'),
    path('rules/', views.rules, name='rules'),
    path('search/', views.search, name='search'),

    # JSON API endpoints (Assignment 9 fetch requirement)
    path('api/bookings/<int:booking_id>/extend/', views.api_extend_booking, name='api_extend_booking'),
    path('api/resources/<int:resource_id>/slots/', views.api_get_slots, name='api_get_slots'),
]
