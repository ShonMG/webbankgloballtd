from django.contrib import admin
from .models import Conversation, Message, MessageTemplate, MessageGroup

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at')
    filter_horizontal = ('participants',)
    search_fields = ('participants__username',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'subject', 'conversation', 'sent_at', 'is_broadcast')
    list_filter = ('is_broadcast', 'sent_at')
    search_fields = ('sender__username', 'subject', 'body')
    raw_id_fields = ('sender', 'conversation')
    filter_horizontal = ('recipients', 'read_by')

@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'created_at')
    search_fields = ('name', 'subject', 'body')

@admin.register(MessageGroup)
class MessageGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    filter_horizontal = ('members',)