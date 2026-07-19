import re

from django.core.management.base import BaseCommand

from apps.jobs.models import Job


class Command(BaseCommand):
    help = "Fix blank lines and empty bullets in existing job descriptions"

    def handle(self, *args, **options):
        updated = 0
        for job in Job.objects.exclude(description="").exclude(description__isnull=True):
            desc = job.description
            lines = desc.split("\n")
            result = []
            in_list = False

            for line in lines:
                stripped = line.strip()
                is_list = stripped.startswith("- ") or bool(re.match(r"^\d+\.\s", stripped))
                is_empty = stripped == "-" or stripped == "- " or bool(re.match(r"^\d+\.\s*$", stripped))

                if is_empty:
                    continue

                if is_list:
                    in_list = True
                    result.append(line)
                elif in_list and stripped == "":
                    continue
                elif in_list and stripped != "" and not is_list:
                    in_list = False
                    result.append(line)
                else:
                    result.append(line)

            new_desc = "\n".join(result)
            if new_desc != desc:
                job.description = new_desc
                job.save(update_fields=["description"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Fixed {updated} job descriptions"))
