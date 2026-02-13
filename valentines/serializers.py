from rest_framework import serializers
from .models import Valentine


class ValentineCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new Valentine"""
    
    class Meta:
        model = Valentine
        fields = [
            'recipient_name',
            'sender_name',
            'sender_location',
            'message',
            'theme',
            'music_link',
            'image_url',
            'template_type',
            'title',
            'image',
            'protection_question',
            'protection_answer',
            'is_premium_tracking',
        ]
    
    def validate_message(self, value):
        """Ensure message is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()


class ValentineDetailSerializer(serializers.ModelSerializer):
    """Serializer for retrieving Valentine details"""
    
    class Meta:
        model = Valentine
        fields = [
            'id',
            'recipient_name',
            'sender_name',
            'message',
            'theme',
            'music_link',
            'image_url',
            'template_type',
            'title',
            'image',
            'slug',
            'is_accepted',
            'views_count',
            'protection_question',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'is_accepted', 'views_count', 'created_at']


class ValentineListSerializer(serializers.ModelSerializer):
    """Serializer for the Wall of Lovers (public feed)"""
    
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Valentine
        fields = [
            'id',
            'sender_name',
            'recipient_name',
            'sender_location',
            'created_at',
            'time_ago',
        ]
    
    def get_time_ago(self, obj):
        """Calculate human-readable time ago"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} min ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = diff.days
            return f"{days} day{'s' if days > 1 else ''} ago"


class ValentineResponseSerializer(serializers.Serializer):
    """Serializer for tracking Valentine responses"""
    accepted = serializers.BooleanField()
    protection_answer = serializers.CharField(required=False, allow_blank=True)

class ValentineManagementSerializer(serializers.ModelSerializer):
    """Serializer for the creator to manage and view stats"""
    class Meta:
        model = Valentine
        fields = [
            'recipient_name',
            'sender_name',
            'management_token',
            'is_accepted',
            'accepted_at',
            'views_count',
            'slug',
            'created_at',
        ]
        read_only_fields = ['management_token', 'is_accepted', 'accepted_at', 'views_count', 'slug', 'created_at']
