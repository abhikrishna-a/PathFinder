from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.core.pagination import StandardPagination


class BaseAPIView(APIView):
    pagination_class = StandardPagination

    def paginate(self, queryset, request):
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return page, paginator

    def success(self, data, status_code=status.HTTP_200_OK):
        return Response(data, status=status_code)

    def error(self, message, status_code=status.HTTP_400_BAD_REQUEST):
        return Response({"error": message}, status=status_code)
