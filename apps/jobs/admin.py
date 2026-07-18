from django.contrib import admin

from .models import Job, Application, SkillLog, DailyStats


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "title", "company", "location", "match_score",
        "status", "source", "fetched_date",
    ]
    list_filter = ["status", "source", "location"]
    search_fields = ["title", "company", "description"]
    readonly_fields = ["fetched_date"]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["job", "status", "sent_at", "skill_match_pct"]
    list_filter = ["status"]
    readonly_fields = ["sent_at"]


@admin.register(SkillLog)
class SkillLogAdmin(admin.ModelAdmin):
    list_display = [
        "skill_name", "job", "found_in_job_desc",
        "highlighted_in_cover_letter",
    ]
    list_filter = ["skill_name", "found_in_job_desc"]


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = [
        "date", "total_fetched", "total_matched",
        "total_applied", "total_ignored", "total_failed",
    ]
    readonly_fields = ["date"]
