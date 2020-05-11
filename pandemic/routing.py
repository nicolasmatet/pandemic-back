from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/pandemic[/]?$', consumers.JoinConsumer),
    re_path(r'ws/pandemic/(?P<room_name>\w+)[/]?$', consumers.PlayConsumer),
]
