from django.urls import path
from telemetry.consumers import EventsConsumer  # we create this next

websocket_urlpatterns = [
    path("ws/events/", EventsConsumer.as_asgi()),
]
