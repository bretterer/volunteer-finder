from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Application


@receiver(post_save, sender=Application)
def check_opportunity_filled(sender, instance, **kwargs):
    """
    When an application is accepted, check if the opportunity should be closed.
    Automatically sets opportunity status to 'filled' when all spots are taken.
    """
    if instance.status == 'accepted':
        instance.opportunity.check_and_update_status()
