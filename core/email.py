from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_email(subject: str, body: str, recipient_list: list[str]) -> bool:
    """
    Send an HTML email with a plain text fallback.

    Args:
        subject: Email subject line
        body: The main message content (inserted into HTML template)
        recipient_list: List of email addresses to send to

    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        html_content = render_to_string('emails/base_email.html', {
            'subject': subject,
            'body': body,
        })

        email = EmailMultiAlternatives(
            subject=subject,
            body=body,  # Plain text fallback
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)
        return True
    except Exception:
        return False
