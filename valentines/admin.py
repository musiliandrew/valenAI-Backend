from django.contrib import admin
from .models import Valentine


@admin.register(Valentine)
class ValentineAdmin(admin.ModelAdmin):
    """Admin interface for Valentine model"""
    
    list_display = [
        'sender_name',
        'recipient_name',
        'theme',
        'is_accepted',
        'views_count',
        'created_at',
        'slug',
    ]
    
    list_filter = [
        'theme',
        'is_accepted',
        'created_at',
    ]
    
    search_fields = [
        'sender_name',
        'recipient_name',
        'slug',
    ]
    
    readonly_fields = [
        'slug',
        'views_count',
        'created_at',
        'updated_at',
        'accepted_at',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('sender_name', 'recipient_name', 'message', 'theme')
        }),
        ('Optional Extras', {
            'fields': ('music_link', 'image_url'),
            'classes': ('collapse',)
        }),
        ('Link & Tracking', {
            'fields': ('slug', 'views_count', 'is_accepted', 'accepted_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
