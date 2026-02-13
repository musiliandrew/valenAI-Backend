from django.db import models
from django.utils.text import slugify
import random
import string


def generate_slug():
    """Generate a unique random slug for Valentine links"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


class Valentine(models.Model):
    """Model to store Valentine's Day messages and configurations"""
    
    THEME_CHOICES = [
        ('classic', 'Classic Rose'),
        ('midnight', 'Midnight Soul'),
        ('golden', 'Golden Love'),
    ]
    
    TEMPLATE_CHOICES = [
        ('classic', 'Classic Gift Box'),
        ('love_letter', 'Love Letter (Premium)'),
        ('poem', 'Romantic Poem (Premium)'),
    ]

    # Basic Info
    recipient_name = models.CharField(max_length=100)
    sender_location = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Nairobi, Kenya")
    sender_name = models.CharField(max_length=100)
    title = models.CharField(max_length=200, blank=True, null=True, help_text="Optional title for Poems or Letters")
    message = models.TextField()
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='classic')
    template_type = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='classic')
    
    # Optional Extras
    music_link = models.URLField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='valentines/', blank=True, null=True)

    # Security & Privacy
    protection_question = models.CharField(max_length=255, blank=True, null=True)
    protection_answer = models.CharField(max_length=255, blank=True, null=True)
    
    # Creator Access & Premium Features
    management_token = models.CharField(max_length=50, unique=True, blank=True)
    is_premium_tracking = models.BooleanField(default=False, help_text="Paid to bypass notification rules")
    
    # Unique Link
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    
    # Tracking
    is_accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    views_count = models.IntegerField(default=0)
    
    # Payment Status
    is_paid = models.BooleanField(default=False)
    is_pending_verification = models.BooleanField(default=False)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    mpesa_phone = models.CharField(max_length=15, blank=True, null=True)
    mpesa_code = models.CharField(max_length=50, blank=True, null=True, unique=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['management_token']),
            models.Index(fields=['-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        import uuid
        if not self.management_token:
            self.management_token = str(uuid.uuid4())[:12] # Short unique token
            
        if not self.slug:
            # Generate unique slug
            base_slug = f"{slugify(self.sender_name)}-loves-{slugify(self.recipient_name)}"
            unique_slug = f"{base_slug}-{generate_slug()}"
            
            # Ensure uniqueness
            while Valentine.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{generate_slug()}"
            
            self.slug = unique_slug
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.sender_name} → {self.recipient_name} ({self.slug})"
    
    def increment_views(self):
        """Increment the view counter"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def mark_accepted(self):
        """Mark the Valentine as accepted"""
        from django.utils import timezone
        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save(update_fields=['is_accepted', 'accepted_at'])
