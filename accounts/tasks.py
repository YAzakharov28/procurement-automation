from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@shared_task
def send_confirm_email_task(context, to_email):
    subject = f"Подтвердите email для пользователя {to_email}"
    html_content = render_to_string("emails/welcome_email.html", context=context)
    text_content = render_to_string("emails/welcome_email.txt", context=context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[to_email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
