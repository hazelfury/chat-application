# ⚡ ChatApp — Real-Time Chat with Django Channels

A real-time multi-room chat application built with Django, Django Channels (WebSocket), SQLite, and Bootstrap 5.

---

## 🗂 Project Structure

```
chat_project/
├── chat_project/
│   ├── settings.py       # Django config + Channels layer
│   ├── asgi.py           # ASGI entry (HTTP + WebSocket routing)
│   └── urls.py           # Top-level URL config
├── chat/
│   ├── models.py         # Room, Message models
│   ├── consumers.py      # WebSocket consumer (connect/receive/send)
│   ├── routing.py        # WS URL patterns
│   ├── views.py          # HTTP views (index, room, create_room)
│   ├── urls.py           # App URL patterns
│   └── templates/chat/   # HTML templates (base, index, room, login)
├── templates/
│   └── base.html         # Shared navbar + layout
├── db.sqlite3            # SQLite database
└── manage.py
```

---

## ✅ Week 1 Deliverables

### Tooling Setup
| Tool | Version | Status |
|---|---|---|
| Python | 3.x | ✅ |
| Django | 6.0.6 | ✅ |
| Django Channels | 4.3.2 | ✅ |
| Daphne (ASGI server) | 4.2.2 | ✅ |
| SQLite | built-in | ✅ |
| Bootstrap | 5.3 (CDN) | ✅ |

### Architecture Decisions
- **ASGI server**: Daphne (replaces Gunicorn for WebSocket support)
- **Channel layer**: InMemoryChannelLayer (Week 1); Redis planned for Week 2
- **Auth**: Django built-in session auth
- **DB**: SQLite for dev simplicity; message history loaded on connect

### Week 1 Update

**What I completed:**
- Designed and documented the full app architecture (models, consumers, routing)
- Set up Django 6 + Django Channels 4.3 + Daphne ASGI server
- Built Room and Message models with SQLite migrations
- Implemented async WebSocket consumer (connect, receive, broadcast, history)
- Created Bootstrap 5 UI: room list, chat room, login, create-room pages
- Seeded 3 default rooms: General, Tech Talk, Random

**What I learned:**
- Django Channels requires ASGI and a channel layer — regular WSGI won't support WebSockets
- `database_sync_to_async` is critical to avoid blocking the async event loop when querying Django ORM
- Daphne handles both HTTP and WS traffic via `ProtocolTypeRouter`
- InMemoryChannelLayer is single-process only; Redis is required for multi-process/production

**What's next (Week 2):**
- Integrate Redis as the channel layer for production-grade pub/sub
- Add user registration page
- Style message bubbles with sender names and timestamps
- Deploy to PythonAnywhere

---

## 🚀 Quick Start

```bash
pip install django channels daphne --break-system-packages
cd chat_project
python manage.py migrate
python manage.py createsuperuser
daphne chat_project.asgi:application
```

Visit `http://localhost:8000` — login with `demo / demo1234`.
