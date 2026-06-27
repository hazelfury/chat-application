from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('room/<slug:room_slug>/', views.room, name='room'),
    path('create-room/', views.create_room, name='create_room'),
]
