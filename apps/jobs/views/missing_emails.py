from apps.jobs.models import Job
from apps.jobs.serializers import JobSerializer
from apps.jobs.views.base import BaseAPIView


class MissingEmailsList(BaseAPIView):
    def get(self, request):
        jobs = (
            Job.objects
            .filter(status="matched", apply_email="")
            .order_by("-match_score")
        )
        serializer = JobSerializer(jobs, many=True)
        return self.success({
            "jobs": serializer.data,
            "total_count": jobs.count(),
        })
