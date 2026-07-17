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


class SkillLog(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="skill_logs"
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="skill_logs")
    skill_name = models.CharField(max_length=100)
    found_in_job_desc = models.BooleanField(default=False)
    highlighted_in_cover_letter = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.skill_name} -> {self.job.company}"


class DailyStats(models.Model):
    date = models.DateField(unique=True)
    total_fetched = models.IntegerField(default=0)
    total_matched = models.IntegerField(default=0)
    total_applied = models.IntegerField(default=0)
    total_ignored = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    top_keywords = models.JSONField(default=list, blank=True)
    top_companies = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Stats for {self.date}"
