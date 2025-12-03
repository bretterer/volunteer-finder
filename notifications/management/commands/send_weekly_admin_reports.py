from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from notifications.utils import get_weekly_report_context


class Command(BaseCommand):
    help = "Send the weekly admin reports email"

    def handle(self, *args, **options):
        User = get_user_model()

        # All staff admins with an email
        admins = User.objects.filter(is_staff=True)
        admin_emails = [u.email for u in admins if u.email]

        if not admin_emails:
            self.stdout.write(self.style.WARNING("No admin emails found."))
            return

        subject = "Weekly Volunteer Finder Admin Report"

        # Build context and render template
        context = get_weekly_report_context()
        html_message = render_to_string("emails/weekly_report.html", context)
        plain_message = strip_tags(html_message)  # fallback text-only version

        send_mail(
            subject,
            plain_message,                     # text version
            settings.DEFAULT_FROM_EMAIL,
            admin_emails,
            html_message=html_message,         # HTML version
            fail_silently=False,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Weekly report sent to: {', '.join(admin_emails)}")
        )
