from django.urls import path

from apps.jobs.views import (
    JobList, JobDetail,
    ApplicationList,
    OverviewStats, SkillStats, CompanyStats, LocationStats,
    WebApplyList, MissingEmailsList, UserProfile,
)
from apps.jobs.views.fetcher import run_fetcher, fetcher_status

api_urlpatterns = [
    # Jobs
    path("jobs/", JobList.as_view(), name="api_job_list"),
    path("jobs/<int:job_id>/", JobDetail.as_view(), name="api_job_detail"),

    # Applications
    path("applications/", ApplicationList.as_view(), name="api_application_list"),

    # Stats
    path("stats/overview/", OverviewStats.as_view(), name="api_overview"),
    path("stats/skills/", SkillStats.as_view(), name="api_skill_stats"),
    path("stats/companies/", CompanyStats.as_view(), name="api_company_stats"),
    path("stats/locations/", LocationStats.as_view(), name="api_location_stats"),

    # Other
    path("web-apply/", WebApplyList.as_view(), name="api_web_apply"),
    path("missing-emails/", MissingEmailsList.as_view(), name="api_missing_emails"),
    path("profile/", UserProfile.as_view(), name="api_profile"),

    # Actions
    path("fetcher/run/", run_fetcher, name="api_run_fetcher"),
    path("fetcher/status/", fetcher_status, name="api_fetcher_status"),
]
