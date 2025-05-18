# PROJECT: Facebook Clone

## MAIN COMPONENTS:
1. User Authentication System
2. Friends System
3. News Feed
4. Real-Time Chat
5. Profile Management

------------------
## 1. USER AUTHENTICATION
------------------
```
FUNCTION register_user():
    GET registration form
    IF form is valid:
        CREATE new user
        LOGIN user
        REDIRECT to home
    ELSE:
        SHOW error messages
    ENDIF

FUNCTION login_user():
    GET login form
    IF credentials valid:
        CREATE session
        REDIRECT to home
    ELSE:
        SHOW error message
    ENDIF

FUNCTION logout_user():
    DESTROY session
    REDIRECT to login
```
------------------
## 2. FRIENDS SYSTEM
------------------
```
CLASS FriendRequest:
    ATTRIBUTES:
        sender (User)
        receiver (User)
        status (pending/accepted/rejected)
        timestamp

FUNCTION send_friend_request(sender, receiver):
    IF no existing request:
        CREATE new FriendRequest
        SEND notification to receiver
    ENDIF

FUNCTION accept_request(request_id):
    UPDATE status to accepted
    ADD users to each other's friends list
    SEND notification to sender

FUNCTION reject_request(request_id):
    UPDATE status to rejected
    SEND notification to sender
```
------------------
## 3. NEWS FEED
------------------
```
FUNCTION get_news_feed(user):
    GET user's friends
    GET posts from user and friends
    ORDER BY timestamp DESC
    RETURN paginated results

FUNCTION create_post(user, content):
    VALIDATE content
    CREATE new Post object
    ADD to news feed
    RETURN success status
```
------------------
## 4. REAL-TIME CHAT
------------------
```
WEBSOCKET HANDLER:
    ON connect:
        AUTHENTICATE user
        JOIN room channel
        SEND connection confirmation

    ON receive_message:
        VALIDATE message
        SAVE to database
        BROADCAST to room
        UPDATE unread count

    ON disconnect:
        LEAVE room channel

FUNCTION get_chat_history(user1, user2):
    FIND chat room between users
    GET last 100 messages
    ORDER BY timestamp ASC
    RETURN messages
```
------------------
## 5. PROFILE MANAGEMENT
------------------
```
FUNCTION view_profile(user_id):
    GET user object
    GET profile info:
        - Bio
        - Profile picture
        - Friends count
        - Recent activity
    RETURN profile data

FUNCTION edit_profile(user, new_data):
    VALIDATE input
    UPDATE profile fields
    SAVE changes
    RETURN updated profile
```
------------------
## MAIN FLOW
------------------
```
WHILE application running:
    HANDLE routes:
        '/' => News Feed
        '/login' => Login
        '/register' => Registration
        '/profile/<username>' => Profile View
        '/messages' => Chat List
        '/messages/<username>' => Chat Room

    HANDLE WebSocket connections:
        '/ws/chat/<room_id>/' => Chat Consumer

    BACKGROUND TASKS:
        - Cleanup expired sessions
        - Send notifications
        - Update online status
```