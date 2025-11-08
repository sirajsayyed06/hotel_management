from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, date, datetime
from django.db.models import Sum
from django.db.models import Max, Count
from hotel.models import *

# Create your views here.
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('/')

@login_required
def dashboard(request):
    # Get basic stats
    total_rooms = Room.objects.count()
    available_rooms = Room.objects.filter(status__iexact='available').count()
    occupied_rooms = Room.objects.filter(status__iexact='occupied').count()
    total_guests = Guest.objects.count()
    
    # Calculate occupancy rate
    occupancy_rate = 0
    if total_rooms > 0:
        occupancy_rate = round((occupied_rooms / total_rooms) * 100, 1)
    
    # Today's revenue (from today's check-ins) - FIXED
    today = date.today()
    today_revenue_result = Booking.objects.filter(
        check_in_date=today,
        status='checked_in'
    ).aggregate(total=Sum('total_amount'))
    
    today_revenue = today_revenue_result['total'] or 0
    
    # Current guests (active check-ins)
    current_guests = CheckIn.objects.filter(is_checked_out=False).count()
    
    # Total bookings
    total_bookings = Booking.objects.count()
    
    # Recent activity (last 10 activities)
    recent_activities = []
    
    # Recent check-ins (last 6 hours)
    recent_checkins = CheckIn.objects.filter(
        actual_check_in__gte=timezone.now() - timedelta(hours=6)
    ).select_related('booking__guest', 'booking__room')[:5]
    
    for checkin in recent_checkins:
        recent_activities.append({
            'type': 'checkin',
            'message': f"{checkin.booking.guest.first_name} checked in to Room {checkin.booking.room.room_number}",
            'time': checkin.actual_check_in,
            'icon': 'fas fa-sign-in-alt'
        })
    
    # Recent bookings (last 6 hours)
    recent_bookings = Booking.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=6)
    ).select_related('guest', 'room')[:5]
    
    for booking in recent_bookings:
        recent_activities.append({
            'type': 'booking',
            'message': f"{booking.guest.first_name} made a reservation for {booking.number_of_nights} nights",
            'time': booking.created_at,
            'icon': 'fas fa-calendar-check'
        })
    
    # Recent check-outs (last 6 hours)
    recent_checkouts = CheckIn.objects.filter(
        actual_check_out__gte=timezone.now() - timedelta(hours=6),
        is_checked_out=True
    ).select_related('booking__guest', 'booking__room')[:5]
    
    for checkout in recent_checkouts:
        recent_activities.append({
            'type': 'checkout',
            'message': f"{checkout.booking.guest.first_name} checked out from Room {checkout.booking.room.room_number}",
            'time': checkout.actual_check_out,
            'icon': 'fas fa-sign-out-alt'
        })
    
    # Sort activities by time (newest first) and take top 6
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    recent_activities = recent_activities[:6]
    
    context = {
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms,
        'total_guests': total_guests,
        'today_checkins': CheckIn.objects.filter(actual_check_in__date=today).count(),
        'occupancy_rate': occupancy_rate,
        'today_revenue': today_revenue,
        'current_guests': current_guests,
        'total_bookings': total_bookings,
        'recent_activities': recent_activities,
    }
    return render(request, "dashboard.html", context)

@login_required
def room_inventory(request):
    if request.method == 'POST':
        room_num = request.POST.get("roomNumber")
        room_name = request.POST.get("roomName").capitalize()
        room_type = request.POST.get("roomType").capitalize()
        capacity = request.POST.get("capacity")
        price_per_night = request.POST.get("price")
        status = request.POST.get("status").capitalize()
        amenities = request.POST.get("amenities").upper()
        description = request.POST.get("description").capitalize()
        
        Room.objects.create(
            room_number=room_num,
            room_name=room_name, 
            room_type=room_type, 
            capacity=capacity, 
            price_per_night=price_per_night, 
            status=status, 
            amenities=amenities, 
            description=description
        )
        messages.success(request, f"Room {room_num} added successfully!")
    return redirect('room_inventory')
    
    rooms = Room.objects.all()
    total_rooms = rooms.count()
    available = rooms.filter(status__iexact='available').count()
    occupied = rooms.filter(status__iexact='occupied').count()
    maintenance = rooms.filter(status__iexact='maintenance').count()

    context = {
        'rooms': rooms,
        'total_rooms': total_rooms,
        'available': available,
        'occupied': occupied,
        'maintenance': maintenance
        }

    return render(request, 'room_inventory.html', context)

@login_required
def edit_room(request, room_number):
    room = get_object_or_404(Room, room_number=room_number)

    if request.method == 'POST':
        room.room_name = request.POST.get('roomName')
        room.room_type = request.POST.get('roomType')
        room.capacity = request.POST.get('capacity')
        room.price_per_night = request.POST.get('price')
        room.status = request.POST.get('status').capitalize()
        room.amenities = request.POST.get('amenities')
        room.description = request.POST.get('description')
        room.save()
        messages.success(request, f"Room {room.room_number} updated successfully!")
        return redirect('room_inventory')

    return render(request, 'edit_room.html', {'room': room})

@login_required
def delete_room(request, room_number):
    room = get_object_or_404(Room, room_number=room_number)
    room.delete()
    messages.success(request, f"Room {room_number} deleted successfully!")
    return redirect('room_inventory')

@login_required
def checkin_view(request):
    rooms = Room.objects.all().order_by('room_number')
    
    # Get room counts
    total_rooms = rooms.count()
    available_count = rooms.filter(status__iexact='available').count()
    occupied_count = rooms.filter(status__iexact='occupied').count()
    maintenance_count = rooms.filter(status__iexact='maintenance').count()
    
    # Get available rooms for dropdown
    available_rooms = Room.objects.filter(status__iexact='available')
    
    # Get today's check-ins
    today = date.today()
    todays_checkins = CheckIn.objects.filter(actual_check_in__date=today, is_checked_out=False)
    
    # Get recent guests
    guests = Guest.objects.all().order_by('-created_at')[:10]
    
    context = {
        'rooms': rooms,
        'available_rooms': available_rooms,
        'todays_checkins': todays_checkins,
        'guests': guests,
        'available_count': available_count,
        'occupied_count': occupied_count,
        'maintenance_count': maintenance_count,
        'total_rooms': total_rooms,
    }
    
    return render(request, 'checkin.html', context)

def process_checkin(request):   
    if request.method == 'POST':
        
            print("Check-in process started...")  # Debug log
            
            # Get form data
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            room_number = request.POST.get('roomNumber')
            checkin_date = request.POST.get('checkinDate')
            checkout_date = request.POST.get('checkoutDate')
            id_proof_type = request.POST.get('id_proof_type', 'Aadhaar')
            id_proof_number = request.POST.get('id_proof_number', '')
            
            print(f"Processing check-in for Room {room_number}")  # Debug log
            
            # Create or get guest
            guest, created = Guest.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone
                }
            )

            if not created:
                guest.first_name = first_name
                guest.last_name = last_name
                guest.phone = phone
                guest.save()
            
            # Get room and verify it's available
            room = Room.objects.get(room_number=room_number)
            print(f"Room {room.room_number} current status: {room.status}")  # Debug log
            
            if room.status.lower() != 'available':
                messages.error(request, f'Room {room_number} is not available! Current status: {room.status}')
                return redirect('checkin_view')
            
            # Calculate number of nights
            checkin_obj = datetime.strptime(checkin_date, '%Y-%m-%d').date()
            checkout_obj = datetime.strptime(checkout_date, '%Y-%m-%d').date()
            nights = (checkout_obj - checkin_obj).days
            
            # Create booking
            booking = Booking.objects.create(
                guest=guest,
                room=room,
                room_type=room.room_type,
                check_in_date=checkin_date,
                check_out_date=checkout_date,
                number_of_guests=1,
                number_of_nights=nights,
                status='checked_in',
                total_amount=room.price_per_night * nights
            )
            
            # Create check-in
            checkin = CheckIn.objects.create(
                booking=booking,
                number_of_guests=1,
                actual_check_in=datetime.now(),
                expected_check_out=datetime.strptime(checkout_date, '%Y-%m-%d'),
                id_proof_type=id_proof_type,
                id_proof_number=id_proof_number
            )
            
            room.status = 'occupied'
            room.save()
            
            print(f"Room {room.room_number} status updated to: {room.status}")

    return redirect('checkin_view')

@login_required
def guest_list(request):
    """Guest management view"""
    guests = Guest.objects.all().order_by('-created_at')
    return render(request, 'guest_list.html', {'guests': guests})

def checkout_view(request):
    """Check-out view with detailed statistics"""
    from django.utils import timezone
    from datetime import date, timedelta
    from django.db.models import Q
    
    today = date.today()
    now = timezone.now()
    
    # Get occupied rooms for dropdown
    occupied_rooms = Room.objects.filter(status__iexact='occupied')
    
    # Get active check-ins (not checked out)
    active_checkins = CheckIn.objects.filter(
        is_checked_out=False
    ).select_related('booking__guest', 'booking__room')
    
    # Calculate statistics
    today_checkouts = CheckIn.objects.filter(
        is_checked_out=True,
        actual_check_out__date=today
    ).count()
    
    pending_checkouts = CheckIn.objects.filter(
        is_checked_out=False,
        expected_check_out__date=today
    ).count()
    
    expected_departures = active_checkins.count()
    
    early_checkouts = CheckIn.objects.filter(
        is_checked_out=True,
        actual_check_out__date=today
    ).filter(
        Q(actual_check_out__time__lt=timezone.datetime.strptime('11:00', '%H:%M').time()) |
        Q(actual_check_out__date__lt=today)
    ).count()
    
    overdue_checkouts = CheckIn.objects.filter(
        is_checked_out=False,
        expected_check_out__date__lt=today
    ).count()
    
    context = {
        'occupied_rooms': occupied_rooms,
        'active_checkins': active_checkins,
        'today_checkouts': today_checkouts,
        'pending_checkouts': pending_checkouts,
        'expected_departures': expected_departures,
        'early_checkouts': early_checkouts,
        'overdue_checkouts': overdue_checkouts,
    }
    return render(request, 'checkout.html', context)

@login_required
def process_checkout(request):
    """Process check-out"""
    if request.method == 'POST':
        try:
            room_number = request.POST.get('roomNumber')
            
            # Find active check-in for this room
            checkin = CheckIn.objects.get(
                booking__room__room_number=room_number,
                is_checked_out=False
            )
            
            # Update check-in
            checkin.actual_check_out = timezone.now()
            checkin.is_checked_out = True
            checkin.save()
            
            # Update room status
            room = checkin.booking.room
            room.status = 'available' 
            room.save()
            
            # Update booking status
            booking = checkin.booking
            booking.status = 'checked_out'
            booking.save()
            
            messages.success(request, f'Check-out successful for Room {room_number}')
            return redirect('checkout_view')
            
        except CheckIn.DoesNotExist:
            messages.error(request, f'No active check-in found for Room {room_number}')
        except Exception as e:
            messages.error(request, f'Check-out failed: {str(e)}')
            
    return redirect('checkout_view')

@login_required
def bookings_view(request):
    bookings = Booking.objects.select_related('guest', 'room').all().order_by('-created_at')
    
    # Get filter parameter
    time_filter = request.GET.get('filter', 'all')
    
    # Calculate date ranges
    today = timezone.now().date()
    
    if time_filter == 'today':
        bookings = bookings.filter(created_at__date=today)
    elif time_filter == 'week':
        start_date = today - timezone.timedelta(days=7)
        bookings = bookings.filter(created_at__date__gte=start_date)
    elif time_filter == 'month':
        start_date = today - timezone.timedelta(days=30)
        bookings = bookings.filter(created_at__date__gte=start_date)
    elif time_filter == '3months':
        start_date = today - timezone.timedelta(days=90)
        bookings = bookings.filter(created_at__date__gte=start_date)
    elif time_filter == '6months':
        start_date = today - timezone.timedelta(days=180)
        bookings = bookings.filter(created_at__date__gte=start_date)
    
    context = {
        'bookings': bookings,
        'current_filter': time_filter,
        'total_bookings': bookings.count(),
    }
    return render(request, 'booking.html', context)

@login_required
def bill_view(request):
    """Bill calculation view - gets data for selected room"""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        room_number = request.GET.get('room_number')
        
        if not room_number:
            return JsonResponse({'error': 'Room number is required'}, status=400)
        
        try:
            # Get the active check-in for this room
            checkin = CheckIn.objects.select_related(
                'booking__guest', 
                'booking__room'
            ).get(
                booking__room__room_number=room_number,
                is_checked_out=False
            )
            
            # Calculate actual nights stayed
            checkin_date = checkin.actual_check_in.date()
            checkout_date = timezone.now().date()
            nights_stayed = (checkout_date - checkin_date).days
            nights_stayed = max(1, nights_stayed)  # At least 1 night
            
            room_rate = checkin.booking.room.price_per_night
            room_total = room_rate * nights_stayed
            
            room_details = {
                'guest_name': f"{checkin.booking.guest.first_name} {checkin.booking.guest.last_name}",
                'room_number': room_number,
                'booking_id': checkin.booking.booking_id,
                'checkin_date': checkin.actual_check_in.strftime("%Y-%m-%d %H:%M"),
                'expected_checkout': checkin.expected_check_out.strftime("%Y-%m-%d %H:%M"),
                'room_rate': float(room_rate),
                'nights_stayed': nights_stayed,
                'room_total': float(room_total),
                'total_amount': float(room_total)
            }
            
            return JsonResponse(room_details)
            
        except CheckIn.DoesNotExist:
            return JsonResponse({'error': 'No active check-in found for this room'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return render(request, 'bill.html')

@login_required
def guest_view(request):
    guests = Guest.objects.annotate(
        last_checkin_date=Max('bookings__checkin__actual_check_in'),
        total_bookings=Count('bookings')
    ).order_by('-created_at')
    
    context = {
        'guests': guests,
    }

    return render(request, 'guest.html', context)
