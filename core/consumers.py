import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import ChatMessage, ChatRoom

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            message = text_data_json['message']
            
            # Save message to database
            message_obj = self.save_message(message)
            
            # Send message to room group
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': str(message_obj.id),
                    'message': message,
                    'user_username': self.scope['user'].username,
                    'timestamp': str(message_obj.timestamp),
                    'is_read': False
                }
            )
        elif message_type == 'typing':
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'typing',
                    'user_username': self.scope['user'].username
                }
            )

    def chat_message(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event))

    def typing(self, event):
        # Send typing notification to WebSocket
        self.send(text_data=json.dumps(event))

    def save_message(self, content):
        room = ChatRoom.objects.get(id=self.room_id)
        return ChatMessage.objects.create(
            room=room,
            sender=self.scope['user'],
            content=content,
            timestamp=timezone.now()
        )