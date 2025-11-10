from django.urls import path
from . import views

urlpatterns = [
    # dashbord as home page
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Manager Pages (all protected)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('rooms/', views.room_inventory, name='room_inventory'),
    path('rooms/<str:room_number>/edit/', views.edit_room, name='edit_room'),
    path('rooms/<str:room_number>/delete/', views.delete_room, name='delete_room'),
    path('checkin/', views.checkin_view, name='checkin_view'),
    path('checkin/process/', views.process_checkin, name='process_checkin'),
    path('checkout/', views.checkout_view, name='checkout_view'),
    path('process-checkout/', views.process_checkout, name='process_checkout'),
    path('guests/', views.guest_list, name='guest_list'),
    path('bookings/',views.bookings_view,name="bookings_view"),
    path('bill/details/', views.bill_view, name='bill_details'),
    path('guests_view/', views.guest_view, name='guest_view'),

    path('payments/', views.payment_management, name='payment_management'),
    path('payments/export/', views.export_payments_csv, name='export_payments_csv'),
    path('revenue-reports/', views.revenue_reports, name='revenue_reports'),
    path('record-payment/<str:booking_id>/', views.record_payment, name='record_payment'),

    path('guests_view/', views.guest_view, name='guest_view'), 
    path('guest/<str:guest_id>/', views.guest_detail_view, name='guest_detail'),
    path('guest/<str:guest_id>/toggle-status/', views.toggle_guest_status, name='toggle_guest_status'),
    path('api/guest-search/', views.guest_search_api, name='guest_search_api'),

    path('guest/<str:guest_id>/toggle-vip/', views.toggle_guest_vip, name='toggle_guest_vip'),
    path('bookings/', views.bookings_management, name='bookings_management'),
    path('bookings/add/', views.add_booking, name='add_booking'),
    path('bookings/cancel/<str:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('bookings/checkin/<str:booking_id>/', views.process_checkin_from_booking, name='process_checkin_from_booking'),
]


