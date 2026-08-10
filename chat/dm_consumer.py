import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import DirectMessage

class DMConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.me = self.scope['user']
        self.other_username = self.scope['url_route']['kwargs']['username']

        if not self.me.is_authenticated:
            await self.close()
            return

        # Create a unique room name for this pair (sorted so both directions match)
        users = sorted([self.me.username, self.other_username])
        self.dm_group = f'dm_{"_".join(users)}'

        await self.channel_layer.group_add(self.dm_group, self.channel_name)
        await self.accept()

        # Load history
        history = await self.get_dm_history()
        for msg in history:
            await self.send(text_data=json.dumps({
                'type': 'history',
                'message': msg['content'],
                'sender': msg['sender'],
                'timestamp': msg['timestamp'],
            }))

        if history:
            await self.send(text_data=json.dumps({
                'type': 'separator',
                'message': f'{len(history)} previous messages loaded',
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.dm_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '').strip()
        if not message:
            return

        saved = await self.save_dm(message)

        # Broadcast message to conversation
        await self.channel_layer.group_send(self.dm_group, {
            'type': 'dm_message',
            'message': message,
            'sender': self.me.username,
            'timestamp': saved['timestamp'],
        })

        # Send notification to receiver
        unread_count = await self.get_receiver_unread_count()
        await self.channel_layer.group_send(
            f'notifications_{self.other_username}',
            {
                'type': 'new_dm_notification',
                'sender': self.me.username,
                'message': message[:50],
                'count': unread_count,
            }
        )

    async def dm_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_dm(self, content):
        receiver = User.objects.get(username=self.other_username)
        msg = DirectMessage.objects.create(
            sender=self.me,
            receiver=receiver,
            content=content,
        )
        return {'timestamp': msg.timestamp.strftime('%H:%M')}

    @database_sync_to_async
    def get_dm_history(self, limit=50):
        other = User.objects.get(username=self.other_username)
        messages = DirectMessage.objects.filter(
            sender=self.me, receiver=other
        ) | DirectMessage.objects.filter(
            sender=other, receiver=self.me
        )
        messages = messages.order_by('timestamp')[:limit]
        return [
            {
                'sender': m.sender.username,
                'content': m.content,
                'timestamp': m.timestamp.strftime('%H:%M'),
            }
            for m in messages
        ]

    @database_sync_to_async
    def get_receiver_unread_count(self):
        from django.contrib.auth.models import User
        receiver = User.objects.get(username=self.other_username)
        return DirectMessage.objects.filter(
            receiver=receiver,
            is_read=False
        ).count()