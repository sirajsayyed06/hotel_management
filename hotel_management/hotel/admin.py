from django.contrib import admin
from hotel.models import Guest, Room, Booking, CheckIn

# Register your models here.
admin.site.register([Guest, Room, Booking, CheckIn])