from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from chat_project.asgi import application
from chat.models import Room, Message, DirectMessage
import json
from asgiref.sync import async_to_sync
from django.test import TransactionTestCase
import asyncio
# ─────────────────────────────────────────────
# UNIT TESTS — Models
# ─────────────────────────────────────────────

class RoomModelTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            name='Test Room',
            slug='test-room',
            description='A test room'
        )

    def test_room_created(self):
        self.assertEqual(self.room.name, 'Test Room')
        self.assertEqual(self.room.slug, 'test-room')

    def test_room_str(self):
        self.assertEqual(str(self.room), 'Test Room')

    def test_room_description(self):
        self.assertEqual(self.room.description, 'A test room')


class MessageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.room = Room.objects.create(name='General', slug='general')
        self.message = Message.objects.create(
            room=self.room,
            user=self.user,
            content='Hello world'
        )

    def test_message_created(self):
        self.assertEqual(self.message.content, 'Hello world')
        self.assertEqual(self.message.user, self.user)
        self.assertEqual(self.message.room, self.room)

    def test_message_str(self):
        self.assertIn('testuser', str(self.message))
        self.assertIn('General', str(self.message))

    def test_message_ordering(self):
        msg2 = Message.objects.create(
            room=self.room, user=self.user, content='Second message'
        )
        messages = list(Message.objects.filter(room=self.room))
        self.assertEqual(messages[0], self.message)
        self.assertEqual(messages[1], msg2)


class DirectMessageModelTest(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(
            username='sender', password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver', password='testpass123'
        )
        self.dm = DirectMessage.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Hello privately'
        )

    def test_dm_created(self):
        self.assertEqual(self.dm.content, 'Hello privately')
        self.assertEqual(self.dm.sender, self.sender)
        self.assertEqual(self.dm.receiver, self.receiver)

    def test_dm_default_unread(self):
        self.assertFalse(self.dm.is_read)

    def test_dm_mark_read(self):
        self.dm.is_read = True
        self.dm.save()
        updated = DirectMessage.objects.get(id=self.dm.id)
        self.assertTrue(updated.is_read)

    def test_dm_str(self):
        self.assertIn('sender', str(self.dm))
        self.assertIn('receiver', str(self.dm))


# ─────────────────────────────────────────────
# INTEGRATION TESTS — Views
# ─────────────────────────────────────────────

class AuthViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_register_page_loads(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create an account')

    def test_register_new_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'WrongPass456!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_valid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)


class RoomViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.room = Room.objects.create(name='General', slug='general')

    def test_index_loads(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'General')

    def test_room_page_loads(self):
        response = self.client.get(reverse('room', args=['general']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'General')

    def test_room_404_for_unknown_slug(self):
        response = self.client.get(reverse('room', args=['nonexistent']))
        self.assertEqual(response.status_code, 404)

    def test_create_room(self):
        response = self.client.post(reverse('create_room'), {
            'name': 'New Room',
            'description': 'A brand new room',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Room.objects.filter(slug='new-room').exists())

    def test_index_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 302)


class DMViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1', password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2', password='testpass123'
        )
        self.client.login(username='user1', password='testpass123')

    def test_dm_inbox_loads(self):
        response = self.client.get(reverse('dm_inbox'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user2')

    def test_dm_conversation_loads(self):
        response = self.client.get(
            reverse('dm_conversation', args=['user2'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user2')

    def test_dm_inbox_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('dm_inbox'))
        self.assertEqual(response.status_code, 302)


# ─────────────────────────────────────────────
# INTEGRATION TESTS — WebSocket Consumers
# ─────────────────────────────────────────────

class ChatConsumerTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='wsuser', password='testpass123'
        )
        self.room = Room.objects.create(
            name='WS Room', slug='ws-room'
        )

    async def test_connect_authenticated(self):
        communicator = WebsocketCommunicator(
            application, '/ws/chat/ws-room/'
        )
        communicator.scope['user'] = self.user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_send_and_receive_message(self):
        communicator = WebsocketCommunicator(
            application, '/ws/chat/ws-room/'
        )
        communicator.scope['user'] = self.user
        await communicator.connect()
        await asyncio.sleep(0.1)

        # Drain all pending messages (online_users etc.)
        while not (await communicator.receive_nothing(timeout=0.2)):
            await communicator.receive_json_from()

        # Send and capture response
        await communicator.send_json_to({'message': 'Hello WebSocket'})
        await asyncio.sleep(0.1)

        # Read responses, skip online_users, find the chat message
        response = None
        for _ in range(5):
            has_message = not (await communicator.receive_nothing(timeout=0.5))
            if not has_message:
                break
            msg = await communicator.receive_json_from()
            if msg.get('type') == 'message':
                response = msg
                break

        self.assertIsNotNone(response)
        self.assertEqual(response['type'], 'message')
        self.assertEqual(response['message'], 'Hello WebSocket')
        self.assertEqual(response['username'], 'wsuser')
        await communicator.disconnect()

    async def test_message_saved_to_db(self):
        communicator = WebsocketCommunicator(
            application, '/ws/chat/ws-room/'
        )
        communicator.scope['user'] = self.user
        await communicator.connect()
        await asyncio.sleep(0.1)

        # Drain initial messages
        while not (await communicator.receive_nothing(timeout=0.2)):
            await communicator.receive_json_from()

        # Send message
        await communicator.send_json_to({'message': 'Saved message'})
        await asyncio.sleep(0.3)

        # Drain responses
        while not (await communicator.receive_nothing(timeout=0.2)):
            await communicator.receive_json_from()

        await communicator.disconnect()

        # Check DB
        count = await sync_to_async(
            Message.objects.filter(content='Saved message').count
        )()
        self.assertEqual(count, 1)
        
class DMConsumerTest(TransactionTestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='dmuser1', password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='dmuser2', password='testpass123'
        )

    async def test_dm_connect(self):
        communicator = WebsocketCommunicator(
            application, '/ws/dm/dmuser2/'
        )
        communicator.scope['user'] = self.user1
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_dm_send_and_receive(self):
        sender = WebsocketCommunicator(
            application, '/ws/dm/dmuser2/'
        )
        receiver = WebsocketCommunicator(
            application, '/ws/dm/dmuser1/'
        )
        sender.scope['user'] = self.user1
        receiver.scope['user'] = self.user2

        await sender.connect()
        await receiver.connect()

        await sender.send_json_to({'message': 'Private hello'})
        response = await receiver.receive_json_from()

        self.assertEqual(response['message'], 'Private hello')
        self.assertEqual(response['sender'], 'dmuser1')

        await sender.disconnect()
        await receiver.disconnect()

    async def test_dm_saved_to_db(self):
        communicator = WebsocketCommunicator(
            application, '/ws/dm/dmuser2/'
        )
        communicator.scope['user'] = self.user1
        await communicator.connect()

        await communicator.send_json_to({'message': 'DB test DM'})
        await communicator.receive_json_from()

        count = await sync_to_async(
            DirectMessage.objects.filter(content='DB test DM').count
        )()
        self.assertEqual(count, 1)
        await communicator.disconnect()


class NotificationConsumerTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='notifuser', password='testpass123'
        )

    async def test_notification_connect(self):
        communicator = WebsocketCommunicator(
            application, '/ws/notifications/'
        )
        communicator.scope['user'] = self.user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'unread_count')
        self.assertEqual(response['count'], 0)

        await communicator.disconnect()