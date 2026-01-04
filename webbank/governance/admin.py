from django.contrib import admin
from .models import Resolution, Vote

@admin.register(Resolution)
class ResolutionAdmin(admin.ModelAdmin):
    list_display = ('title', 'vote_type', 'is_active', 'deadline', 'yes_votes', 'no_votes', 'created_by', 'creation_date')
    list_filter = ('is_active', 'vote_type', 'votable_by_gold_only', 'pool')
    search_fields = ('title', 'description')
    date_hierarchy = 'creation_date'
    raw_id_fields = ('created_by', 'pool') # Use raw_id_fields for FKs

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('resolution', 'voter', 'vote_choice', 'vote_date')
    list_filter = ('vote_choice', 'vote_date', 'resolution__title')
    search_fields = ('resolution__title', 'voter__username')
    date_hierarchy = 'vote_date'
    raw_id_fields = ('resolution', 'voter')
