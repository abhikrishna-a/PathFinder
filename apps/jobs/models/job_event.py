from django.db import models


class JobEvent(models.Model):
    EVENT_TYPES = [
        ("fetched", "Fetched"),
        ("matched", "Matched"),
        ("applied", "Applied"),
        ("web_apply", "Web Apply"),
        ("ignored", "Ignored"),
        ("status_changed", "Status Changed"),
    ]

    job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES, db_index=True)
    old_status = models.CharField(max_length=20, default="")
    new_status = models.CharField(max_length=20, default="")
    match_score = models.FloatField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event_type} for {self.job.title} ({self.created_at})"
