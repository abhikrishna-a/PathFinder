from django.db import models


class Job(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("matched", "Matched"),
        ("applied", "Applied"),
        ("web_apply", "Web Apply"),
        ("ignored", "Ignored"),
        ("failed", "Failed"),
    ]

    title = models.CharField(max_length=500)
    company = models.CharField(max_length=300, db_index=True)
    location = models.CharField(max_length=300, blank=True, default="")
    description = models.TextField(blank=True, default="")
    source = models.CharField(max_length=50, blank=True, default="")
    posted_date = models.CharField(max_length=200, blank=True, default="")
    fetched_date = models.DateTimeField(auto_now_add=True)
    match_score = models.FloatField(default=0, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new", db_index=True)
    apply_email = models.EmailField(blank=True, default="")
    apply_url = models.URLField(blank=True, default="")
    search_query = models.CharField(max_length=200, blank=True, default="")
    matched_skills = models.JSONField(default=list, blank=True)
    skill_score_breakdown = models.JSONField(default=dict, blank=True)
    skill_gaps = models.JSONField(default=list, blank=True)
    filter_reason = models.CharField(max_length=500, blank=True, default="")
    match_explanation = models.TextField(blank=True, default="")
    job_url = models.URLField(blank=True, default="")
    uid = models.CharField(max_length=500, unique=True)
    salary = models.IntegerField(default=0, db_index=True)
    salary_display = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        ordering = ["-match_score", "-fetched_date"]

    def __str__(self):
        return f"{self.title} at {self.company} ({self.match_score}%)"
