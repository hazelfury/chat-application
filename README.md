# ⚡ ChatApp — Real-Time Chat Application

A full-featured real-time chat application built with Django Channels, WebSockets, Redis, SQLite, and Bootstrap 5.

🔗 **Live Demo:** https://YOUR-RAILWAY-URL.up.railway.app

---

## Features

- 💬 **Real-time multi-room chat** via WebSocket
- 👤 **User registration and authentication**
- 📜 **Message history** with pagination (Load More)
- 🟢 **Online/offline user status** indicators
- 📩 **Private direct messaging** between users
- 🔔 **Notification system** — toast popups, badge counts, tab title alerts
- ✅ **31 unit and integration tests** covering models, views, and consumers
- 🚀 **Deployed on Railway** with Redis channel layer

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0.6 |
| WebSocket | Django Channels 4.3.2 |
| ASGI Server | Daphne 4.1.2 |
| Channel Layer | Redis (channels-redis 4.2.0) |
| Database | SQLite |
| Frontend | Bootstrap 5.3 |
| Deployment | Railway |

---

## Project Structure
chat_project/
├── chat_project/
│ ├── settings.py # Django config + channel layers
│ ├── asgi.py # ASGI routing (HTTP + WebSocket)
│ └── urls.py # Top-level URL config
├── chat/
│ ├── models.py # Room, Message, DirectMessage
│ ├── consumers.py # ChatConsumer (room WebSocket)
│ ├── dm_consumer.py # DMConsumer (private messages)
│ ├── notification_consumer.py # NotificationConsumer
│ ├── routing.py # WebSocket URL patterns
│ ├── views.py # HTTP views + pagination API
│ ├── forms.py # RegisterForm
│ ├── urls.py # App URL patterns
│ ├── admin.py # Admin registration
│ ├── tests.py # 31 unit + integration tests
│ └── templates/chat/ # HTML templates
├── templates/
│ └── base.html # Shared navbar + notifications
├── requirements.txt
├── railway.json
└── manage.py


---

## Local Setup

### Prerequisites
- Python 3.12
- Redis running locally

### Steps

```bash
# Clone the repo
git clone https://github.com/hazelfury/chat-application.git
cd chat-application

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser

# Start Redis (Windows)
redis-server

# Start the server (Windows PowerShell)
$env:DJANGO_SETTINGS_MODULE="chat_project.settings"; daphne chat_project.asgi:application
```

Visit `http://localhost:8000`

---

## Run Tests

```bash
python manage.py test chat --verbosity=2
```

Expected: `Ran 31 tests — OK`

---

## Deployment

Deployed on **Railway** with:
- Daphne as ASGI server
- Redis as managed channel layer service
- Environment variables: `DJANGO_SETTINGS_MODULE`, `SECRET_KEY`, `DJANGO_DEBUG`

---

## Weekly Progress

| Week | Feature |
|---|---|
| Week 1 | Django + Channels setup, architecture, room/message models |
| Week 2 | User registration + Django Auth login |
| Week 3 | Room model enhancements — message count, creator tracking |
| Week 4 | WebSocket consumer + message timestamps |
| Week 5 | SQLite message saving + history loading |
| Week 6 | Online/offline status indicators + Redis channel layer |
| Week 7 | Private messaging (direct messages) |
| Week 8 | Notification system — toasts, badges, tab title |
| Week 9 | Unit and integration tests (31 passing) |
| Week 10 | Message pagination with Load More |
| Week 11 | Production deployment on Railway |
| Week 12 | Final testing + documentation |