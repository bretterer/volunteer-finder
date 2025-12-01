from django.core.management.base import BaseCommand
from django.utils import timezone

from opportunities.models import Opportunity


class Command(BaseCommand):
    help = 'Expire opportunities that have passed their end date'

    def handle(self, *args, **options):
        today = timezone.now().date()

        # Find all active opportunities with an end date that has passed
        expired_opportunities = Opportunity.objects.filter(
            status='active',
            end_date__lt=today
        )

        count = expired_opportunities.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No opportunities to expire.'))
            return

        # Update all matching opportunities to expired status
        expired_opportunities.update(status='expired')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully expired {count} opportunit{"y" if count == 1 else "ies"}.')
        )
