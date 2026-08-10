import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import DirectMessage

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f'notifications_{self.user.username}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send unread count on connect
        unread = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread,
        }))

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Mark messages as read when user opens a DM conversation
        if data.get('type') == 'mark_read':
            sender_username = data.get('sender')
            await self.mark_messages_read(sender_username)
            unread = await self.get_unread_count()
            await self.send(text_data=json.dumps({
                'type': 'unread_count',
                'count': unread,
            }))

    async def new_dm_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_dm',
            'sender': event['sender'],
            'message': event['message'],
            'count': event['count'],
        }))

    async def unread_count_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': event['count'],
        }))

    @database_sync_to_async
    def get_unread_count(self):
        return DirectMessage.objects.filter(
            receiver=self.user,
            is_read=False
        ).count()

    @database_sync_to_async
    def mark_messages_read(self, sender_username):
        from django.contrib.auth.models import User
        try:
            sender = User.objects.get(username=sender_username)
            DirectMessage.objects.filter(
                sender=sender,
                receiver=self.user,
                is_read=False
            ).update(is_read=True)
        except User.DoesNotExist:
            pass