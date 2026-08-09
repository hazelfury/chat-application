from django.urls import re_path
from . import consumers
from . import dm_consumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_slug>[\w-]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/dm/(?P<username>[\w-]+)/$', dm_consumer.DMConsumer.as_asgi()),
]