from django.db import models


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
