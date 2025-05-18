from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Post, Comment, FriendRequest, Notification, ChatRoom, ChatMessage

# Register your models here.
class CustomUserAdmin(UserAdmin):
    list_display = ('user_id', 'username', 'first_name', 'last_name', 'email', 'last_login', 'date_joined', 'is_staff')
    readonly_fields = ('user_id',)
    fieldsets = (
        (None, {'fields': ('user_id', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'profile_picture', 'bio')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Friends', {'fields': ('friends',)}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(FriendRequest)
admin.site.register(Notification)
admin.site.register(ChatRoom)
admin.site.register(ChatMessage)