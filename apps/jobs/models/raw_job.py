import uuid

from django.db import models


class RawJob(models.Model):
    uid = models.CharField(max_length=500, db_index=True)
    title = models.CharField(max_length=500)
    company = models.CharField(max_length=300, db_index=True)
    location = models.CharField(max_length=300, default="")
    description = models.TextField(default="")
    source = models.CharField(max_length=50, default="")
    posted_date = models.CharField(max_length=200, default="")
    apply_url = models.URLField(default="")
    search_query = models.CharField(max_length=200, default="")
    salary = models.IntegerField(default=0)
    salary_display = models.CharField(max_length=50, default="")
    full_text = models.TextField(default="")
    fetch_batch_id = models.CharField(max_length=100, db_index=True, default="")
    fetched_at = models.DateTimeField(auto_now_add=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-fetched_at"]

    def __str__(self):
        return f"{self.title} at {self.company} [{self.source}]"

    @staticmethod
    def new_batch_id() -> str:
        return uuid.uuid4().hex[:12]
