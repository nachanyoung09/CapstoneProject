# app/socket_handlers.py (Updated to use DB for chat history)
from flask_socketio import SocketIO, emit, join_room
from flask import request
from app import db
from app.models.chat import Chatroom, Message
from flask_jwt_extended import get_jwt_identity
from datetime import datetime


def register_socketio_handlers(socketio: SocketIO):
    @socketio.on('join')
    def handle_join(data):
        # JWT에서 사용자 ID 가져오기
        user_id = get_jwt_identity()
        room_id = data['roomid']
        join_room(room_id)

        # 입장 메시지 브로드캐스트
        emit('message', {
            'user': 'System',
            'msg': f'User {user_id} joined room {room_id}.'
        }, to=room_id)

        # 이전 메시지 조회 (DB)
        history = Message.query.filter_by(chatroom_id=room_id) \
            .order_by(Message.timestamp) \
            .all()
        history_data = [
            {'user': m.sender_id, 'msg': m.content, 'timestamp': m.timestamp.isoformat()}
            for m in history
        ]
        emit('chat_history', history_data, to=request.sid)

    @socketio.on('message')
    def handle_message(data):
        # JWT에서 사용자 ID 가져오기
        user_id = get_jwt_identity()
        room_id = data['roomid']
        content = data['msg']

        # 메시지 저장
        new_msg = Message(
            chatroom_id=room_id,
            sender_id=user_id,
            content=content,
            timestamp=datetime.utcnow()
        )
        db.session.add(new_msg)
        db.session.commit()

        # 브로드캐스트
        emit('message', {
            'user': user_id,
            'msg': content,
            'timestamp': new_msg.timestamp.isoformat()
        }, to=room_id)
