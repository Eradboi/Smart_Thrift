import pyotp
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from .models import *
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

# function for otp
def send_otp(request,username):
    totp = pyotp.TOTP(pyotp.random_base32(), interval=600)
    otp = totp.now()
    request.session['otp_secret_key'] = totp.secret
    valid_date = datetime.now() + timedelta(minutes=10)
    request.session['otp_valid_date'] = str(valid_date)
    userName =  username
    recipient_name=get_object_or_404(User, username=userName).email
    custom_message=otp
    subject = 'Smart Thrift Verification Code'
    from_email = 'settings.EMAIL_HOST_USER'
    to_email = [get_object_or_404(User, username=username).email]

    # HTML content with CSS styling
    html_content = render_to_string('accounts/email_template.html', {'recipient_name': recipient_name, 'custom_message': custom_message})


    email = EmailMessage(subject, html_content, from_email, to_email)
    email.content_subtype = 'html'
    email.send(fail_silently=False)
        






