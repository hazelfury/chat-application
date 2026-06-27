import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Room, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        self.room_group_name = f'chat_{self.room_slug}'

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Send last 20 messages on connect
        messages = await self.get_recent_messages()
        for msg in messages:
            await self.send(text_data=json.dumps({
                'type': 'history',
                'message': msg['content'],
                'username': msg['user__username'],
                'timestamp': msg['timestamp'].strftime('%H:%M'),
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '').strip()
        if not message:
            return

        user = self.scope['user']
        if not user.is_authenticated:
            return

        # Save to DB
        await self.save_message(user, message)

        # Broadcast to group
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat_message',
            'message': message,
            'username': user.username,
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username'],
        }))

    @database_sync_to_async
    def get_recent_messages(self):
        try:
            room = Room.objects.get(slug=self.room_slug)
            return list(room.messages.select_related('user').values('content', 'user__username', 'timestamp').order_by('-timestamp')[:20])[::-1]
        except Room.DoesNotExist:
            return []

    @database_sync_to_async
    def save_message(self, user, content):
        room = Room.objects.get(slug=self.room_slug)
        Message.objects.create(room=room, user=user, content=content)
