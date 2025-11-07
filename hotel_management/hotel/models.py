from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
import uuid
from django.core.validators import MinValueValidator

ROOM_TYPES = [
    ('standard', 'Standard'),
    ('double', 'Double'),
    ('suite', 'Suite'),
    ('family', 'Family'),
    ('delux','Delux'),
    ('executive','Executive'),
]

ROOM_STATUSES = [
    ('available', 'Available'),
    ('occupied', 'Occupied'),
    ('maintenance', 'Maintenance'),
    ('out_of_service', 'Out of Service'),
]

class Guest(models.Model):
    guest_id = models.CharField(max_length=20, primary_key=True, editable=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(unique=True)
    address = models.TextField(blank=True)
    loyalty_id = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.guest_id:
            self.guest_id = "CLT" + uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name_plural = 'Guests'

    def __str__(self):
        return f"{self.guest_id} | {self.first_name} {self.last_name}"

class Room(models.Model):
    # room_id = models.CharField(primary_key=True)
    room_number = models.CharField(primary_key=True)
    room_name=models.CharField(max_length=20,default="standard")
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    capacity = models.PositiveIntegerField(default=2, validators=[MinValueValidator(1)])
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ROOM_STATUSES, default='available')
    amenities = models.JSONField(default=dict, blank=True)
    description=models.TextField(default="Great")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['room_number']
        indexes = [models.Index(fields=['status', 'room_type'])]

    def __str__(self):
        return f"Room {self.room_number} ({self.get_room_type_display()})"

class Booking(models.Model):
    booking_id = models.CharField(max_length=20, primary_key=True, editable=False)
    guest = models.ForeignKey('Guest', on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='bookings')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_guests = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    number_of_nights=models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=ROOM_STATUSES, default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = "BKG" + uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.booking_id}"

class CheckIn(models.Model):
    checkin_id = models.CharField(max_length=20, primary_key=True, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='checkin')
    actual_check_in = models.DateTimeField(default=timezone.now)
    expected_check_out = models.DateTimeField(default=timezone.now)
    actual_check_out = models.DateTimeField(null=True, blank=True)
    number_of_guests = models.PositiveIntegerField(default=1)
    id_proof_type = models.CharField(max_length=20, choices=[('aadhaar', 'Aadhaar Card')], default='aadhaar')
    id_proof_number = models.CharField(max_length=50)
    is_checked_out = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.checkin_id:
            self.checkin_id = "CHK" + uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"CheckIn {self.checkin_id}"