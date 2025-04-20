from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction
from .utils import check_and_unlock_modes

@receiver(post_save, sender=Transaction)
def trigger_mode_unlock(sender, instance, created, **kwargs):
    if created:
        check_and_unlock_modes(instance.user)
