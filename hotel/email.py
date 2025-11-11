# from django.http import HttpResponse
# from django.core.mail import send_mail
# def send_test_email(request):
#     subject = "Test Email from Django + Brevo"
#     message = "Hello! This is a test email sent using Brevo SMTP from Django."
#     from_email = "manthans889@gmail.com"
#     recipient_list = ["sirajsayyed06@gmail.com"]

#     try:
#         send_mail(subject, message, from_email, recipient_list)
#         return HttpResponse("Email sent successfully!")
#     except Exception as e:
#         return HttpResponse(f"Error: {e}")

from django.http import HttpResponse
from django.core.mail import send_mail

def send_test_email(request, name, email, room_number, checkin_date, checkout_date, total_amount):
    subject = "Confirmation Email from Hotel Management"
    message = "Dear {},\n\nYour booking has been confirmed!\n\nDetails:\nRoom Number: {}\nCheck-in Date: {}\nCheck-out Date: {}\nTotal Amount: ${}\n\nThank you for choosing our hotel!".format(name, room_number, checkin_date, checkout_date, total_amount)
    from_email = "manthans889@gmail.com"
    recipient_list = [email]

    try:
        send_mail(subject, message, from_email, recipient_list)
        return HttpResponse("Email sent successfully!")
    except Exception as e:
        return HttpResponse(f"Error: {e}")