from django.urls import path
from . import views

urlpatterns = [
    path("", views.overview, name="overview"),
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:job_id>/", views.job_detail, name="job_detail"),
    path("applications/", views.application_list, name="application_list"),
    path("web-apply/", views.web_apply_list, name="web_apply_list"),
    path("missing-emails/", views.missing_emails, name="missing_emails"),
    path("stats/skills/", views.skill_stats, name="skill_stats"),
    path("stats/companies/", views.company_stats, name="company_stats"),
    path("stats/locations/", views.location_stats, name="location_stats"),
    path("profile/", views.profile_view, name="profile"),
]
