from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractUser
import os

def user_profile_pic_path(instance, filename):
    # Get file extension
    ext = filename.split('.')[-1]
    # Rename file as username.ext
    filename = f"{instance.username}.{ext}"
    # Return the full path
    return os.path.join('profile_pics', filename)

def user_post_pic_path(instance, filename):
    """
    Correct signature: Django passes the model instance and filename
    - instance: The Post model instance
    - filename: Original uploaded filename
    """
    ext = filename.split('.')[-1]
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"post_{instance.user.username}_{timestamp}.{ext}"
    return os.path.join('post_pics', filename)

class User(AbstractUser):
    # Custom primary key field
    user_id = models.AutoField(primary_key=True)
    profile_picture = models.ImageField(
        upload_to=user_profile_pic_path,
        default='default_profile_pic.png'
    )
    bio = models.TextField(max_length=500, blank=True)
    email = models.EmailField(unique=True, null=False, blank=False)
    friends = models.ManyToManyField('self', symmetrical=True, blank=True)

    def __str__(self):
        return self.username or str(self.user_id)
    
    def get_unread_notifications_count(self):
        return self.notifications_received.filter(is_read=False).count()

class Post(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # References your custom user model
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.TextField()
    post_picture = models.ImageField(
        upload_to=user_post_pic_path,
        blank=True,
        null=True
    )
    timestamp = models.DateTimeField(default=timezone.now)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_posts',
        blank=True
    )

class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.id}'

class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='friend_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='friend_requests_received', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ], default='pending')

    class Meta:
        unique_together = ['from_user', 'to_user']

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('friend_request', 'Friend Request'),
        ('friend_accept', 'Friend Request Accepted'),
        ('post_like', 'Post Like'),
    )

    recipient = models.ForeignKey(User, related_name='notifications_received', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='notifications_sent', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

class ChatRoom(models.Model):
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(default=timezone.now)

    def get_chat_name(self, user):
        """Get other participant's name for display"""
        return self.participants.exclude(id=user.id).first().username

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']