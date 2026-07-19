from django.urls import re_path

from apps.jobs.consumers import FetcherProgressConsumer

websocket_urlpatterns = [
    re_path(r"ws/fetcher/progress/$", FetcherProgressConsumer.as_asgi()),
]
