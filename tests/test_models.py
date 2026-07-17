import pytest
from apps.jobs.models import Job, Application, DailyStats, SkillLog


@pytest.mark.django_db
class TestJobModel:
    def test_create_job(self, sample_job):
        assert sample_job.title == "Python Developer"
        assert sample_job.company == "TechCorp"
        assert sample_job.status == "new"

    def test_job_str(self, sample_job):
        assert "Python Developer" in str(sample_job)
        assert "TechCorp" in str(sample_job)

    def test_job_ordering(self, db):
        from django.utils import timezone
        import datetime

        job1 = Job.objects.create(
            title="Job 1", company="A", uid="uid-1", match_score=80
        )
        job2 = Job.objects.create(
            title="Job 2", company="B", uid="uid-2", match_score=90
        )
        jobs = list(Job.objects.all())
        assert jobs[0].match_score >= jobs[1].match_score


@pytest.mark.django_db
class TestApplicationModel:
    def test_create_application(self, sample_application):
        assert sample_application.job.company == "TechCorp"
        assert sample_application.status == "sent"

    def test_application_str(self, sample_application):
        assert "TechCorp" in str(sample_application)


@pytest.mark.django_db
class TestDailyStatsModel:
    def test_create_stats(self, db):
        from datetime import date
        stats = DailyStats.objects.create(
            date=date.today(),
            total_fetched=100,
            total_matched=20,
            total_applied=5,
        )
        assert stats.total_fetched == 100
        assert str(stats) == f"Stats for {date.today()}"


@pytest.mark.django_db
class TestSkillLogModel:
    def test_create_skill_log(self, db, sample_job, sample_application):
        log = SkillLog.objects.create(
            application=sample_application,
            job=sample_job,
            skill_name="django",
            found_in_job_desc=True,
            highlighted_in_cover_letter=True,
        )
        assert log.skill_name == "django"
        assert log.found_in_job_desc is True
