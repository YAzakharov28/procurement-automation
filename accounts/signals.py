from typing import Type

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import ConfirmEmailToken
from accounts.tasks import send_confirm_email_task

User = get_user_model()


@receiver(signal=post_save, sender=User)
def send_confirm_token(sender: Type[User], instance: User, created: bool, **kwargs):
    """
    отправляем письмо с подтрердждением почты
    """
    if created and not instance.is_active:
        token, _ = ConfirmEmailToken.objects.get_or_create(user_id=instance.pk)

        context = {
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "key": token.key,
        }
        send_confirm_email_task.delay(context=context, to_email=instance.email)
