from collections import OrderedDict

from rest_framework.response import Response
from rest_framework.pagination import BasePagination


class StandardPagination(BasePagination):
    page_size = 50
    page_query_param = "page"
    page_size_query_param = None
    max_page_size = 200

    def paginate_queryset(self, queryset, request, view=None):
        from django.core.paginator import Paginator

        page_number = request.query_params.get(self.page_query_param, 1)
        try:
            page_number = int(page_number)
        except (TypeError, ValueError):
            page_number = 1

        paginator = Paginator(queryset, self.page_size)
        try:
            self.page = paginator.page(page_number)
        except Exception:
            from django.core.paginator import EmptyPage
            self.page = paginator.page(1)

        self.request = request
        return self.page.object_list

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ("count", self.page.paginator.count),
            ("page", self.page.number),
            ("total_pages", self.page.paginator.num_pages),
            ("next", self.page.has_next()),
            ("previous", self.page.has_previous()),
            ("results", data),
        ]))
