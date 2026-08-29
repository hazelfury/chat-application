from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('room/<slug:room_slug>/', views.room, name='room'),
    path('create-room/', views.create_room, name='create_room'),
    path('register/', views.register, name='register'),
    path('dm/', views.dm_inbox, name='dm_inbox'),
    path('dm/<str:username>/', views.dm_conversation, name='dm_conversation'),
    path('api/messages/<slug:room_slug>/', views.load_more_messages, name='load_more_messages'),  # NEW
    path('api/dm/<str:username>/', views.load_more_dms, name='load_more_dms'),  # NEW
]