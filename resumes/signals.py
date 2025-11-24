from django.db.models.signals import post_save
from django.dispatch import receiver
import threading


def score_opportunity_async(opportunity_id):
    """Score all resumes against new opportunity in background thread"""
    import time
    time.sleep(1)

    try:
        from resumes.models import Resume, ResumeScore
        from opportunities.models import Opportunity
        from resumes.services import ResumeScoringService

        try:
            opportunity = Opportunity.objects.get(id=opportunity_id)
        except Opportunity.DoesNotExist:
            print(f"⚠️ Opportunity {opportunity_id} no longer exists")
            return

        service = ResumeScoringService()
        resumes = Resume.objects.exclude(extracted_text='').exclude(extracted_text__isnull=True)

        count = 0
        for resume in resumes:
            if not ResumeScore.objects.filter(resume=resume, opportunity_id=opportunity_id).exists():
                try:
                    service.score_resume_for_opportunity(resume, opportunity)
                    count += 1
                except Exception as e:
                    print(f"  ❌ Error scoring {resume}: {e}")

        print(f"✅ Scored {count} resumes against new opportunity")

    except Exception as e:
        print(f"❌ Scoring error: {e}")


@receiver(post_save, sender='opportunities.Opportunity')
def score_new_opportunity(sender, instance, created, **kwargs):
    """Auto-score all resumes against new opportunity when added"""
    if created:
        print(f"🆕 New opportunity detected: {instance.title}")
        thread = threading.Thread(target=score_opportunity_async, args=(instance.id,))
        thread.daemon = True
        thread.start()