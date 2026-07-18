from django.db import models

from .job import Job


class Application(models.Model):
    STATUS_CHOICES = [
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("bounced", "Bounced"),
        ("web_apply", "Web Apply"),
    ]

    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name="application")
    sent_at = models.DateTimeField(auto_now_add=True)
    email_subject = models.CharField(max_length=500, blank=True, default="")
    cover_letter_text = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="sent")
    error_message = models.TextField(blank=True, default="")
    skills_highlighted = models.JSONField(default=list, blank=True)
    skills_in_job_desc = models.JSONField(default=list, blank=True)
    skill_match_pct = models.FloatField(default=0)
    criteria_data = models.JSONField(default=dict, blank=True)
    skill_gaps = models.JSONField(default=list, blank=True)
    match_explanation = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Application to {self.job.company} - {self.status}"
