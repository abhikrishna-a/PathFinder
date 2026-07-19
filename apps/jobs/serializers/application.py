from rest_framework import serializers

from apps.jobs.models import Application
from apps.jobs.serializers.job import JobSerializer


class ApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "job", "sent_at", "status", "email_subject",
            "cover_letter_text", "error_message",
            "skills_highlighted", "skills_in_job_desc", "skill_match_pct",
            "criteria_data", "skill_gaps", "match_explanation",
        ]
