import re

from django.core.management.base import BaseCommand

from apps.jobs.models import Job
from apps.jobs.services import _extract_salary_from_text
from common.utils import html_to_markdown


class Command(BaseCommand):
    help = "Re-extract salaries and convert HTML descriptions to markdown for existing jobs"

    def handle(self, *args, **options):
        salary_updated = 0
        desc_updated = 0

        for job in Job.objects.all():
            changed = False

            if not job.salary and job.description:
                salary, salary_display = _extract_salary_from_text(
                    f"{job.description}"
                )
                if salary:
                    job.salary = salary
                    job.salary_display = salary_display
                    changed = True
                    salary_updated += 1

            if job.description and "<" in job.description:
                job.description = html_to_markdown(job.description)
                changed = True
                desc_updated += 1

            if changed:
                job.save(update_fields=["salary", "salary_display", "description"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated salary: {salary_updated}, descriptions: {desc_updated}"
            )
        )
