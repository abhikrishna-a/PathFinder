from django.db import models

from .job import Job
from .application import Application


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
