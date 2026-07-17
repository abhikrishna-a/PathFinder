import pytest
from apps.jobs.matcher import match_job, match_all_jobs


class TestMatchJob:
    def test_match_python_job(self):
        job = {
            "title": "Python Developer",
            "company": "TechCorp",
            "location": "Kerala, India",
            "description": "Looking for Python developer with Django experience",
            "uid": "test-uid-001",
        }
        result = match_job(job)
        assert "match_score" in result
        assert result["match_score"] > 0

    def test_match_non_python_job(self):
        job = {
            "title": "Java Developer",
            "company": "BigCorp",
            "location": "Bangalore",
            "description": "Looking for Java developer with Spring Boot",
            "uid": "test-uid-002",
        }
        result = match_job(job)
        assert result["match_score"] == 0

    def test_match_empty_description(self):
        job = {
            "title": "Python Developer",
            "company": "TechCorp",
            "location": "Remote",
            "description": "",
            "uid": "test-uid-003",
        }
        result = match_job(job)
        assert "match_score" in result


class TestMatchAllJobs:
    def test_match_multiple_jobs(self):
        jobs = [
            {
                "title": "Python Developer",
                "company": "TechCorp",
                "location": "Kerala",
                "description": "Python Django developer",
                "uid": "test-uid-010",
            },
            {
                "title": "Python Backend Engineer",
                "company": "StartupCo",
                "location": "Remote India",
                "description": "Python FastAPI developer",
                "uid": "test-uid-011",
            },
        ]
        results = match_all_jobs(jobs)
        assert len(results) == 2
        assert all(r["match_score"] > 0 for r in results)

    def test_match_empty_list(self):
        results = match_all_jobs([])
        assert results == []
