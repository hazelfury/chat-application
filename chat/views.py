from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from .models import Room

@login_required
def index(request):
    rooms = Room.objects.all().order_by('name')
    return render(request, 'chat/index.html', {'rooms': rooms})

@login_required
def room(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)
    return render(request, 'chat/room.html', {'room': room})

@login_required
def create_room(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            slug = slugify(name)
            Room.objects.get_or_create(slug=slug, defaults={'name': name, 'description': description})
            return redirect('room', room_slug=slug)
    return render(request, 'chat/create_room.html')
