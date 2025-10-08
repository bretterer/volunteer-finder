from django.db import models
from accounts.models import User
from opportunities.models import Opportunity

# Create your models here.

class MatchScore(models.Model):
    """
    Stores match scores between volunteers and opportunities.
    This will be used by the recommendation engine.
    """
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_scores')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='match_scores')
    score = models.FloatField(help_text="Match score from 0.0 to 1.0")
    skill_match = models.FloatField(default=0.0)
    availability_match = models.FloatField(default=0.0)
    interest_match = models.FloatField(default=0.0)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'match_scores'
        unique_together = ['volunteer', 'opportunity']
        ordering = ['-score']

    def __str__(self):
        return f"{self.volunteer.username} <-> {self.opportunity.title}: {self.score:.2f}"
