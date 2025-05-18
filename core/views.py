from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db.models import Count, Q
from django.db.models.expressions import OuterRef, Subquery
from django.db import transaction
from django.db.models import Prefetch
from logging import Logger

from .models import User, Post, Comment, FriendRequest, Notification, ChatRoom, ChatMessage

logger = Logger(__name__)

# Create your views here.
@login_required(login_url='core:login')
def index(request):
    return render(request, 'post_feed.html')


def signup(request):
    if request.method == 'POST':
        try:
            user_name = request.POST.get('user_name')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password != confirm_password:
                raise ValueError('Passwords do not match!')
            
            if User.objects.filter(email=email).exists():
                raise ValueError('This Email is already taken!')
            
            if User.objects.filter(username=user_name).exists():
                raise ValueError('This User Name is already taken!')

            user = User.objects.create_user(
                username=user_name,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password
            )
            user.save()

            # Authenticate and log the user in to his/her home page
            user_login = auth.authenticate(username=user_name, password=password)
            auth.login(request, user_login)

            return redirect('core:index')

        except ValueError as e:
            print(str(e))
            return redirect('core:signup')
        except Exception as e:
            print(str(e))
            return redirect('core:signup')

    return render(request, 'authentication/signup.html')


def login(request):
    if request.method == 'POST':
        try:
            user_name = request.POST.get('user_name')
            password = request.POST.get('password')

            user = auth.authenticate(username=user_name, password=password)
            if user is None:
                raise ValueError('Invalid User Data!')
            
            auth.login(request, user)
            return redirect('core:index')

        except ValueError as e:
            print(str(e))
            return redirect('core:login')
        except Exception as e:
            print(str(e))
            return redirect('core:login')

    return render(request, 'authentication/login.html')


@login_required(login_url='core:login')
def logout(request):
    auth.logout(request)
    return redirect('core:login')


@login_required(login_url='core:login')
def profile(request, username=None):
    try:
        # Get profile user
        profile_user = request.user if username is None else User.objects.get(username=username)

        # Get posts for the profile user
        posts = Post.objects.filter(user=profile_user) \
                          .select_related('user') \
                          .prefetch_related('likes') \
                          .annotate(like_count=Count('likes')) \
                          .order_by('-timestamp')
        
        # Check friendship status
        is_friend = request.user.friends.filter(username=profile_user.username).exists()
        
        # Check for pending sent request
        pending_request = FriendRequest.objects.filter(
            from_user=request.user,
            to_user=profile_user,
            status='pending'
        ).exists()
        
        # Check for received friend request
        received_request = FriendRequest.objects.filter(
            from_user=profile_user,
            to_user=request.user,
            status='pending'
        ).exists()

        context = {
            'profile_user': profile_user,
            'posts': posts,
            'user_has_liked': {
                post.id: post.likes.filter(username=request.user.username).exists()
                for post in posts
            } if request.user.is_authenticated else {},
            'is_friend': is_friend,
            'pending_request': pending_request,
            'received_request': received_request,
        }

        return render(request, 'profile/profile.html', context)

    except User.DoesNotExist:
        print("User not found!")
        return redirect('core:index')
    except Exception as e:
        print(f"Error loading profile: {str(e)}")
        return redirect('core:index')


@login_required(login_url='core:login')
def profile_edit(request):
    user = request.user
    
    if request.method == 'POST':
        try:
            # Handle file upload separately
            if 'profile_picture' in request.FILES:
                old_pic = user.profile_picture
                # Delete old profile picture if it's not default
                if old_pic and old_pic.name != 'default_profile_pic.png':
                    default_storage.delete(old_pic.path)
                user.profile_picture = request.FILES['profile_picture']
            
            # Update other fields
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.bio = request.POST.get('bio', user.bio)
            
            user.save()
            print('Profile updated successfully!')
            return redirect('core:profile')
            
        except Exception as e:
            print(f'Error updating profile: {str(e)}')
            return redirect('core:profile_edit')

    # For GET requests, show the edit form with current values
    context = {
        'user': user,
        'current_bio': user.bio,
    }
    return render(request, 'profile/profile_edit.html', context)


@login_required(login_url='core:login')
def post(request):
    posts = Post.objects.select_related('user') \
                    .prefetch_related('likes') \
                    .annotate(like_count=Count('likes')) \
                    .order_by('-timestamp')

    if request.method == 'POST':
        try:
            caption = request.POST.get('content', '')
            image = request.FILES.get('post_image')
            
            # if not image:
            #     raise ValueError('Image is required!')
            
            # Create new post
            post = Post.objects.create(
                user=request.user,
                content=caption,
                post_picture=image
            )
            post.save()

            print('Post created successfully!')
            return redirect('core:post')
            
        except ValueError as e:
            print(str(e))
            return redirect('core:post')
        except Exception as e:
            print(f'Error creating post: {str(e)}')
            return redirect('core:post')

    context = {
        'posts': posts,
        'user_has_liked': {
            post.id: post.likes.filter(username=request.user.username).exists()
            for post in posts
        } if request.user.is_authenticated else {}
    }

    return render(request, 'post_feed.html', context)


@login_required(login_url='core:login')
def delete_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id, user=request.user)
        if post.post_picture:
            default_storage.delete(post.post_picture.path)
        post.delete()
        print('Post deleted successfully!')
    except Post.DoesNotExist:
        print('Post not found or you do not have permission to delete it.')
    except Exception as e:
        print(f'Error deleting post: {str(e)}')

    return redirect('core:post')


@login_required(login_url='core:login')
def like_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        
        if post.likes.filter(username=request.user.username).exists():
            # User has already liked the post - remove like
            post.likes.remove(request.user)
            print('Post unliked successfully!')
        else:
            # User hasn't liked the post - add like
            post.likes.add(request.user)
            print('Post liked successfully!')

        # Create notification only if the post author is not the same as the liker
        if post.user != request.user:
            Notification.objects.create(
                recipient=post.user,
                sender=request.user,
                notification_type='post_like',
                message='liked your post',
                post=post
            )

        return redirect('core:post')
        
    except Post.DoesNotExist:
        print('Post not found.')
        return redirect('core:post')
    except Exception as e:
        print(f'Error processing like: {str(e)}')
        return redirect('core:post')


@login_required(login_url='core:login')
def add_comment(request, post_id):
    if request.method == 'POST':
        try:
            post = Post.objects.get(id=post_id)
            content = request.POST.get('content')
            
            if not content:
                raise ValueError('Comment content is required!')
            
            Comment.objects.create(
                user=request.user,
                post=post,
                content=content
            )

            print('Comment added successfully!')

        except Post.DoesNotExist:
            print('Post not found.')
        except ValueError as e:
            print(str(e))
        except Exception as e:
            print(f'Error adding comment: {str(e)}')

    return redirect(request.META.get('HTTP_REFERER', 'core:post'))


@login_required(login_url='core:login')
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id, user=request.user)
        comment.delete()
        print('Comment deleted successfully!')
    except Comment.DoesNotExist:
        print('Comment not found or you do not have permission to delete it.')
    except Exception as e:
        print(f'Error deleting comment: {str(e)}')

    return redirect(request.META.get('HTTP_REFERER', 'core:post'))


@login_required(login_url='core:login')
def send_friend_request(request, username):
    try:
        to_user = User.objects.get(username=username)
        
        if to_user == request.user:
            return redirect('core:profile', username=username)
        
        if request.user.friends.filter(username=username).exists():
            return redirect('core:profile', username=username)
        
        # Check if a request already exists
        if FriendRequest.objects.filter(
            from_user=request.user,
            to_user=to_user,
            status='pending'
        ).exists():
            messages.info(request, "Friend request already sent!")
            return redirect('core:profile', username=username)
        
        FriendRequest.objects.create(
            from_user=request.user,
            to_user=to_user
        )
        
        # Create notification
        Notification.objects.create(
            recipient=to_user,
            sender=request.user,
            notification_type='friend_request',
            message='sent you a friend request'
        )

    except User.DoesNotExist:
        print("User not found!")
    except Exception as e:
        print(f"Error sending friend request: {str(e)}")

    return redirect('core:profile', username=username)

@login_required(login_url='core:login')
def accept_friend_request(request, username):
    try:
        from_user = User.objects.get(username=username)
        
        # Find and validate friend request
        friend_request = FriendRequest.objects.get(
            from_user=from_user,
            to_user=request.user,
            status='pending'
        )
        
        # Add both users as friends
        request.user.friends.add(from_user)
        friend_request.status = 'accepted'
        friend_request.save()
        
        # Create chat room for the new friends
        chat_room = ChatRoom.objects.create()
        chat_room.participants.add(request.user, from_user)
        
        # Create notification for accepted request
        Notification.objects.create(
            recipient=from_user,
            sender=request.user,
            notification_type='friend_accept',
            message='accepted your friend request'
        )

        logger.info(f"User {request.user.username} accepted friend request from {username} and created chat room")
        messages.success(request, f"You are now friends with {from_user.username}!")
        
    except User.DoesNotExist:
        logger.error(f"User {username} not found")
        messages.error(request, "User not found!")
    except FriendRequest.DoesNotExist:
        logger.error(f"Friend request from {username} not found")
        messages.error(request, "Friend request not found!")
    except Exception as e:
        logger.error(f"Error accepting friend request: {str(e)}")
        messages.error(request, f"Error accepting friend request: {str(e)}")
    
    return redirect('core:profile', username=username)

@login_required(login_url='core:login')
def remove_friend(request, username):
    try:
        friend = User.objects.get(username=username)
        
        if not request.user.friends.filter(username=username).exists():
            messages.error(request, "You are not friends with this user!")
            return redirect('core:profile', username=username)
        
        # Remove from friends list (symmetrical=True will handle both directions)
        request.user.friends.remove(friend)
        
        # Delete friend request records in both directions
        FriendRequest.objects.filter(
            from_user__in=[request.user, friend],
            to_user__in=[request.user, friend],
            status='accepted'
        ).delete()
        
        # Delete chat room between these users
        ChatRoom.objects.filter(participants=request.user).filter(participants=friend).delete()
        
        logger.info(f"Removed {friend.username} from friends and deleted chat room")
        messages.success(request, f"Removed {friend.username} from friends!")
        
    except User.DoesNotExist:
        logger.error("User not found!")
        messages.error(request, "User not found!")
    except Exception as e:
        logger.error(f"Error removing friend: {str(e)}")
        messages.error(request, f"Error removing friend: {str(e)}")

    return redirect('core:profile', username=username)

@login_required(login_url='core:login')
def decline_friend_request(request, username):
    try:
        from_user = User.objects.get(username=username)
        
        # Find and delete the friend request
        friend_request = FriendRequest.objects.get(
            from_user=from_user,
            to_user=request.user,
            status='pending'
        )
        friend_request.delete()

        print(f"Friend request from {from_user.username} declined!")

    except User.DoesNotExist:
        print("User not found!")
    except FriendRequest.DoesNotExist:
        print("Friend request not found!")
    except Exception as e:
        print(f"Error declining friend request: {str(e)}")

    return redirect('core:profile', username=username)

@login_required(login_url='core:login')
def cancel_friend_request(request, username):
    try:
        to_user = User.objects.get(username=username)
        
        # Find and delete the pending friend request
        friend_request = FriendRequest.objects.get(
            from_user=request.user,
            to_user=to_user,
            status='pending'
        )
        friend_request.delete()

        print(f"Friend request to {to_user.username} cancelled!")

    except User.DoesNotExist:
        print("User not found!")
    except FriendRequest.DoesNotExist:
        print("Friend request not found!")
    except Exception as e:
        print(f"Error cancelling friend request: {str(e)}")
    
    return redirect('core:profile', username=username)


@login_required(login_url='core:login')
def friends_list(request, username=None):
    try:
        # Get the user whose friends list to display
        user = request.user if username is None else User.objects.get(username=username)
        
        # Get all friends of the user with their profile info
        friends = user.friends.all()
        
        context = {
            'friends': friends,
            'view_user': user,  # The user whose friends we're viewing
            'is_own_friends_list': user == request.user
        }
        
        print(f"Displaying friends list for user {user.username}")
        return render(request, 'friends_list.html', context)
        
    except User.DoesNotExist:
        print(f"Attempted to view friends list for non-existent user {username}")
        return redirect('core:index')
    except Exception as e:
        print(f"Error displaying friends list: {str(e)}")
        return redirect('core:index')


@login_required(login_url='core:login')
def notifications(request):
    try:
        # Get user's notifications
        notifications = Notification.objects.filter(recipient=request.user)\
            .select_related('sender', 'post')\
            .order_by('-timestamp')

        # Mark notifications as read
        notifications.update(is_read=True)

        context = {
            'notifications': notifications
        }

        print(f"User {request.user.username} viewed their notifications")
        return render(request, 'notifications.html', context)

    except Exception as e:
        print(f"Error loading notifications: {str(e)}")
        return redirect('core:index')


@login_required(login_url='core:login')
def chat_list(request):
    try:
        # Get all chat rooms the user is participating in
        chat_rooms = ChatRoom.objects.filter(participants=request.user)\
            .prefetch_related('participants')\
            .annotate(
                last_message=Subquery(
                    ChatMessage.objects.filter(room_id=OuterRef('id'))
                    .order_by('-timestamp')
                    .values('content')[:1]
                ),
                last_message_time=Subquery(
                    ChatMessage.objects.filter(room_id=OuterRef('id'))
                    .order_by('-timestamp')
                    .values('timestamp')[:1]
                ),
                unread_count=Count(
                    'messages',
                    filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
                )
            ).order_by('-last_message_time')
        
        logger.debug(f"Found {chat_rooms.count()} chat rooms for user {request.user.username}")

        # Prepare chat room data with other participants
        # global formatted_chats
        formatted_chats = []
        existing_chat_users = set()  # Track users we already have chats with

        for room in chat_rooms:
            try:
                # Get all other participants
                other_users = room.participants.exclude(username=request.user.username)
                if not other_users.exists():
                    logger.warning(f"Chat room {room.id} has no other participants")
                    continue
                    
                # Create a chat entry for each other participant
                for other_user in other_users:
                    logger.debug(f"Processing chat with {other_user.username} - {room.unread_count} unread messages")
                    existing_chat_users.add(other_user.username)
                    
                    formatted_chats.append({
                        'room': room,
                        'other_user': other_user,
                        'last_message': room.last_message or "No messages yet",
                        'last_message_time': room.last_message_time,
                        'unread_count': room.unread_count,
                        'profile_picture_url': other_user.profile_picture.url if other_user.profile_picture else None,
                        'has_existing_chat': True
                    })
            except Exception as e:
                logger.error(f"Error processing chat room {room.id}: {str(e)}")
                continue

        # Get all users (except current user) who don't have existing chats
        all_users = User.objects.exclude(username=request.user.username)
        users_without_chats = all_users.exclude(username__in=existing_chat_users)
        
        # Add users without existing chats to the list
        for user in users_without_chats:
            formatted_chats.append({
                'other_user': user,
                'last_message': "No messages yet",
                'last_message_time': None,
                'unread_count': 0,
                'profile_picture_url': user.profile_picture.url if user.profile_picture else None,
                'has_existing_chat': False
            })

        # Sort all chats/users by username
        formatted_chats.sort(key=lambda x: x['other_user'].username)

        context = {
            'formatted_chats': formatted_chats,
            'active_chat': False,
            'has_chats': len(formatted_chats) > 0,
            'all_users_count': all_users.count()
        }
        
        logger.info(f"Successfully prepared chat list for {request.user.username}")
        return render(request, 'messages.html', context)
        
    except Exception as e:
        logger.error(f"Critical error in chat_list view: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred while loading your chats. Please try again.")
        return redirect('core:index')

@login_required(login_url='core:login')
def chat_room(request, username):
    try:
        logger.info(f"User {request.user.username} accessing chat with {username}")
        
        # Get other user
        try:
            other_user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.warning(f"User {username} not found")
            return redirect('core:messages')

        # Get or create chat room
        try:
            room = ChatRoom.objects.filter(participants=request.user)\
                                 .filter(participants=other_user)\
                                 .distinct().first()
            
            if not room:
                with transaction.atomic():
                    room = ChatRoom.objects.create()
                    room.participants.add(request.user, other_user)
                    logger.info(f"Created new chat room {room.id} between {request.user.username} and {other_user.username}")
        except Exception as e:
            logger.error(f"Error creating/fetching chat room: {str(e)}", exc_info=True)
            messages.error(request, "Error accessing chat room")
            return redirect('core:messages')

        # Mark messages as read
        try:
            updated = ChatMessage.objects.filter(
                room=room,
                sender=other_user,
                is_read=False
            ).update(is_read=True)
            logger.debug(f"Marked {updated} messages as read")
        except Exception as e:
            logger.error(f"Error marking messages as read: {str(e)}")

        # Get all chat rooms for sidebar in same format as chat_list view
        try:
            chat_rooms = ChatRoom.objects.filter(participants=request.user)\
                .prefetch_related('participants')\
                .annotate(
                    last_message=Subquery(
                        ChatMessage.objects.filter(room_id=OuterRef('id'))
                        .order_by('-timestamp')
                        .values('content')[:1]
                    ),
                    last_message_time=Subquery(
                        ChatMessage.objects.filter(room_id=OuterRef('id'))
                        .order_by('-timestamp')
                        .values('timestamp')[:1]
                    ),
                    unread_count=Count(
                        'messages',
                        filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
                    )
                ).order_by('-last_message_time')

            # Create formatted_chats in same structure as chat_list view
            formatted_chats = []
            for chat_room in chat_rooms:
                try:
                    other_users = chat_room.participants.exclude(username=request.user.username)
                    if not other_users.exists():
                        continue
                        
                    for other_user_obj in other_users:
                        formatted_chats.append({
                            'room': chat_room,
                            'other_user': other_user_obj,
                            'last_message': chat_room.last_message or "No messages yet",
                            'last_message_time': chat_room.last_message_time,
                            'unread_count': chat_room.unread_count,
                            'profile_picture_url': other_user_obj.profile_picture.url if other_user_obj.profile_picture else None,
                            'is_active': chat_room.id == room.id  # Mark current chat as active
                        })
                except Exception as e:
                    logger.error(f"Error formatting chat room {chat_room.id}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching chat rooms: {str(e)}", exc_info=True)
            formatted_chats = []
            messages.error(request, "Error loading your conversations")

        # Get messages for current chat
        try:
            messages_list = room.messages.select_related('sender').order_by('timestamp')[:100]
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}")
            messages_list = []
            messages.error(request, "Error loading messages")

        context = {
            'formatted_chats': formatted_chats,  # Now using same structure as chat_list
            'active_chat': True,
            'other_user': {
                'username': other_user.username,
                'profile_picture_url': other_user.profile_picture.url if other_user.profile_picture else None,
                'is_online': other_user.is_online() if hasattr(other_user, 'is_online') else False
            },
            'messages': messages_list,
            'room_id': room.id,
            'has_messages': bool(messages_list)
        }
        
        logger.info(f"Successfully loaded chat room for {request.user.username} with {other_user.username}")
        return render(request, 'messages.html', context)
        
    except Exception as e:
        logger.critical(f"Unexpected error in chat_room view: {str(e)}", exc_info=True)
        messages.error(request, "An unexpected error occurred")
        return redirect('core:messages')