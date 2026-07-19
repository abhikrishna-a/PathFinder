from django.core.management.base import BaseCommand

from apps.jobs.models import Job
from apps.jobs.services import _extract_salary_from_text


class Command(BaseCommand):
    help = "Extract salary from description text for all jobs with salary=0"

    def handle(self, *args, **options):
        jobs = Job.objects.filter(salary=0).exclude(description="")
        self.stdout.write(f"Checking {jobs.count()} jobs with salary=0...")

        updated = 0
        no_salary = 0
        distribution = {}

        for job in jobs:
            text = f"{job.title} {job.description[:800]}"
            salary, salary_display = _extract_salary_from_text(text)

            if salary:
                job.salary = salary
                job.salary_display = salary_display
                job.save(update_fields=["salary", "salary_display"])
                updated += 1
                bucket = salary_display
            else:
                no_salary += 1
                bucket = "none"

            distribution[bucket] = distribution.get(bucket, 0) + 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Updated {updated} jobs, {no_salary} still have no salary."
        ))

        self.stdout.write("\nSalary distribution:")
        for label, count in sorted(distribution.items(), key=lambda x: -x[1]):
            self.stdout.write(f"  {label}: {count}")
