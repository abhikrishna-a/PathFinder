from rest_framework import serializers

from apps.jobs.models import Job


class JobSerializer(serializers.ModelSerializer):
    has_failed_app = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id", "title", "company", "location", "source",
            "posted_date", "fetched_date", "match_score", "status",
            "matched_skills", "salary", "salary_display",
            "job_url", "uid", "apply_email", "apply_url", "has_failed_app",
        ]

    def get_has_failed_app(self, obj):
        return getattr(obj, "has_failed_app", False)


class JobDetailSerializer(serializers.ModelSerializer):
    skill_gaps = serializers.JSONField()
    skill_score_breakdown = serializers.JSONField()
    match_explanation = serializers.CharField()
    filter_reason = serializers.CharField()
    application = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id", "title", "company", "location", "description", "source",
            "posted_date", "fetched_date", "match_score", "status",
            "matched_skills", "skill_score_breakdown", "skill_gaps",
            "salary", "salary_display", "apply_email", "apply_url",
            "job_url", "uid", "search_query", "filter_reason",
            "match_explanation", "application",
        ]

    def get_application(self, obj):
        try:
            app = obj.application
            from apps.jobs.serializers import ApplicationSerializer
            return ApplicationSerializer(app).data
        except Exception:
            return None


class JobListQuerySerializer(serializers.Serializer):
    status = serializers.CharField(default="all", required=False)
    location = serializers.CharField(default="all", required=False)
    salary = serializers.CharField(default="all", required=False)
    sort = serializers.CharField(default="-match_score", required=False)
    search = serializers.CharField(default="", required=False)
    page = serializers.IntegerField(default=1, required=False)
