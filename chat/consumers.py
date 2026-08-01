import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Room, Message

# In-memory set to track online users per room
online_users = {}

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        self.room_group_name = f'chat_{self.room_slug}'
        self.username = self.scope['user'].username if self.scope['user'].is_authenticated else 'Anonymous'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Add user to online set for this room
        if self.room_slug not in online_users:
            online_users[self.room_slug] = set()
        online_users[self.room_slug].add(self.username)

        # Broadcast updated online users list to room
        await self.broadcast_online_users()

        # Send message history
        history = await self.get_message_history()
        for msg in history:
            await self.send(text_data=json.dumps({
                'type': 'history',
                'username': msg['username'],
                'message': msg['content'],
                'timestamp': msg['timestamp'],
            }))

        if history:
            await self.send(text_data=json.dumps({
                'type': 'separator',
                'message': f'{len(history)} previous messages loaded',
            }))

        # Announce user joined
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'user_join',
            'username': self.username,
        })

    async def disconnect(self, close_code):
        # Remove user from online set
        if self.room_slug in online_users:
            online_users[self.room_slug].discard(self.username)

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Broadcast updated online users list
        await self.broadcast_online_users()

        # Announce user left
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'user_leave',
            'username': self.username,
        })

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = self.username

        saved = await self.save_message(username, message)

        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat_message',
            'message': message,
            'username': username,
            'timestamp': saved['timestamp'],
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'username': event['username'],
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'username': event['username'],
        }))

    async def online_users_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': event['users'],
        }))

    async def broadcast_online_users(self):
        users = list(online_users.get(self.room_slug, set()))
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'online_users_update',
            'users': users,
        })

    @database_sync_to_async
    def save_message(self, username, message):
        room = Room.objects.get(slug=self.room_slug)
        user = User.objects.filter(username=username).first()
        msg = Message.objects.create(room=room, user=user, content=message)
        return {'timestamp': msg.timestamp.strftime('%H:%M')}

    @database_sync_to_async
    def get_message_history(self, limit=50):
        room = Room.objects.get(slug=self.room_slug)
        messages = Message.objects.filter(room=room).order_by('timestamp')[:limit]
        return [
            {
                'username': m.user.username if m.user else 'Anonymous',
                'content': m.content,
                'timestamp': m.timestamp.strftime('%H:%M'),
            }
            for m in messages
        ]