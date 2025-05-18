from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.post, name='index'),

    # User Authentication
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    # User profile
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/', views.profile, name='profile'),

    # Post operations
    path('post/', views.post, name='post'),
    path('post/<int:post_id>/del/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),

    # Friend operations
    path('send-friend-request/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('accept-friend-request/<str:username>/', views.accept_friend_request, name='accept_friend_request'),
    path('remove-friend/<str:username>/', views.remove_friend, name='remove_friend'),
    path('decline-friend-request/<str:username>/', views.decline_friend_request, name='decline_friend_request'),
    path('cancel-friend-request/<str:username>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('friends/', views.friends_list, name='friends_list'),

    # Notifications
    path('notifications/', views.notifications, name='notifications'),

    # Chat operations
    path('messages/', views.chat_list, name='messages'),
    path('messages/<str:username>/', views.chat_room, name='chat_room'),
]