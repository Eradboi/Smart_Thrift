from django.template import Context
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings



def send_register_email(name, email, category):
    context = {
        'name': name,
        'email': email,
        'category': category,
    }
    subject = 'Welcome To Smart Thrift!'
    from_email = 'settings.EMAIL_HOST_USER'
    to_email = [email]

    # HTML content with CSS styling
    html_content = render_to_string('accounts/email_welcome.html', context)


    email = EmailMessage(subject, html_content, from_email, to_email)
    email.content_subtype = 'html'
    return email.send(fail_silently=False)