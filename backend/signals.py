from django.dispatch import Signal, receiver

from backend.tasks import send_order_confirmed_emails_task

order_confirmed = Signal()


@receiver(order_confirmed)
def send_order_confirmed_emails(sender, order, **kwargs):
    send_order_confirmed_emails_task.delay(order.id)
