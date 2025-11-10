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
    is_vip = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.guest_id:
            self.guest_id = "CLT" + uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    @property
    def last_checkin(self):
        """Get the most recent check-in for this guest"""
        latest_booking = self.bookings.order_by('-check_in_date').first()
        if latest_booking and hasattr(latest_booking, 'checkins'):
            latest_checkin = latest_booking.checkins.order_by('-actual_check_in').first()
            return latest_checkin
        return None

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

PAYMENT_STATUSES = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
    ('partially_refunded', 'Partially Refunded'),
]

PAYMENT_METHODS = [
    ('cash', 'Cash'),
    ('card', 'Credit/Debit Card'),
    ('upi', 'UPI'),
    ('net_banking', 'Net Banking'),
    ('wallet', 'Digital Wallet'),
]

class Payment(models.Model):
    payment_id = models.CharField(max_length=20, primary_key=True, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUSES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Payment timing
    payment_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateField(blank=True, null=True)
    
    # Additional fields for better tracking
    payment_type = models.CharField(max_length=20, choices=[
        ('advance', 'Advance Payment'),
        ('final', 'Final Payment'),
        ('refund', 'Refund'),
        ('additional', 'Additional Charges'),
    ], default='advance')
    
    description = models.TextField(blank=True)
    created_by = models.CharField(max_length=100, blank=True)  # Store staff username
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = "PMT" + uuid.uuid4().hex[:12].upper()
        
        # Auto-update booking amount_paid when payment is completed
        if self.payment_status == 'completed' and self.booking:
            self.booking.amount_paid = self.booking.amount_paid + self.amount
            self.booking.save()
        
        # Auto-update booking amount_paid when payment is refunded
        elif self.payment_status in ['refunded', 'partially_refunded'] and self.booking:
            self.booking.amount_paid = self.booking.amount_paid - self.amount
            self.booking.save()
            
        super().save(*args, **kwargs)

    @property
    def balance_after_payment(self):
        """Calculate balance after this payment"""
        previous_payments = Payment.objects.filter(
            booking=self.booking, 
            payment_status='completed',
            payment_date__lt=self.payment_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        return self.booking.total_amount - (previous_payments + self.amount)

    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['payment_status', 'payment_date']),
            models.Index(fields=['guest', 'payment_date']),
            models.Index(fields=['booking', 'payment_status']),
        ]

    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount} ({self.get_payment_status_display()})"

