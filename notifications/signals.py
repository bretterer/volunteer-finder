from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail

from opportunities.models import Opportunity
from notifications.models import Notification


@receiver(post_save, sender=Opportunity)
def notify_org_on_opportunity_creation(sender, instance, created, **kwargs):
    if not created:
        return  # avoid triggering on updates

    org = instance.organization  # adjust if your field name is different
    org_email = org.email

    # --- 1) SEND EMAIL ---
    subject = "New Opportunity Created"
    message = (
        f"Hello {org.username},\n\n"
        f"You have created a new opportunity:\n\n"
        f"Title: {instance.title}\n"
        f"Description: {instance.description}\n\n"
        f"Thank you for using Volunteer Finder!"
    )

    send_mail(
        subject,
        message,
        None,            # uses DEFAULT_FROM_EMAIL
        [org_email],
        fail_silently=False,
    )

    # --- 2) OPTIONAL: Create an in-app notification for the org user ---
    Notification.objects.create(
        user=org,  # depends on your model, change if needed
        notification_type='new_opportunity',
        title=f"New Opportunity Created: {instance.title}",
        message=f"A new opportunity was created in your organization.",
        email_sent=True,
    )
