from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('new_conversation/', views.new_conversation, name='new_conversation'),
    path('send_message/<int:conversation_id>/', views.send_message, name='send_message'),
    path('broadcast/', views.send_broadcast_message, name='send_broadcast_message'),

    # Message Templates
    path('templates/', views.message_template_list, name='message_template_list'),
    path('templates/create/', views.message_template_create, name='message_template_create'),
    path('templates/update/<int:pk>/', views.message_template_update, name='message_template_update'),
    path('templates/delete/<int:pk>/', views.message_template_delete, name='message_template_delete'),
]