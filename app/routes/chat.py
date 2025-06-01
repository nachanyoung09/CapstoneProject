# app/routes/chat.py (라우트 코드 수정)
from flask import Blueprint, request, jsonify,render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.chat import Chatroom, Message, TradePromise
from datetime import datetime

bp_chat = Blueprint('chat', __name__, url_prefix='/api/v1/chatrooms')

# 채팅방 목록 조회
@bp_chat.route('', methods=['GET'])
@jwt_required()
def view_chatrooms():
    
    user_id = int(get_jwt_identity())
    chatrooms = Chatroom.query.filter(
        Chatroom.participant_ids.contains(user_id)
    ).all()
    result = [{
        'chatroomId': c.id,
        'name': c.name,
        'lastMessage': c.last_message,
        'updatedAt': c.updated_at.isoformat()
    } for c in chatrooms]
    return jsonify({'chatrooms': result}), 200

# 채팅방 생성
@bp_chat.route('', methods=['POST'])
@jwt_required()
def create_chatroom():
    from app import db
    user_id = int(get_jwt_identity())
    data = request.get_json()
    participant_ids = data.get('participantIds')  # list of ints
    related_post_id = data.get('relatedPostId')
    name = data.get('name')
    if not all([participant_ids, related_post_id, name]):
        return jsonify({'message': '필수 항목 누락'}), 400
    new_chatroom = Chatroom(
        name=name,
        participant_ids=participant_ids,
        related_post_id=related_post_id,
        updated_at=datetime.utcnow()
    )
    db.session.add(new_chatroom)
    db.session.commit()
    return jsonify({
        'chatroomId': new_chatroom.id,
        'name': new_chatroom.name,
        'createdAt': new_chatroom.updated_at.isoformat()
    }), 201

# 채팅방 상세 조회
@bp_chat.route('/<int:chatroomid>/info', methods=['GET'])
@jwt_required()
def chatroom_info(chatroomid):
    user_id = int(get_jwt_identity())
    chatroom = Chatroom.query.get(chatroomid)
    if not chatroom:
        return jsonify({'message': '채팅방을 찾을 수 없습니다.'}), 404
    if user_id not in chatroom.participant_ids:
        return jsonify({'message': '조회 권한이 없습니다.'}), 403

    return jsonify({
        'chatroomId': chatroom.id,
        'name': chatroom.name,
        'participants': chatroom.participant_ids,
        'updatedAt': chatroom.updated_at.isoformat()
    }), 200

# 채팅 메시지 목록 조회
@bp_chat.route('/<int:chatroomid>/messages', methods=['GET'])
@jwt_required()
def view_chatroom_messages(chatroomid):
    user_id = int(get_jwt_identity())
    chatroom = Chatroom.query.get(chatroomid)
    if not chatroom:
        return jsonify({'message': '채팅방을 찾을 수 없습니다.'}), 404
    # 권한 확인
    if user_id not in chatroom.participant_ids:
        return jsonify({'message': '조회 권한이 없습니다.'}), 403
    limit = request.args.get('limit', type=int, default=50)
    before = request.args.get('before')

    query = Message.query.filter_by(chatroom_id=chatroomid)
    if before:
        before_dt = datetime.fromisoformat(before)
        query = query.filter(Message.timestamp < before_dt)

    messages = query.order_by(Message.timestamp.desc()).limit(limit).all()
    result = [{
        'messageId': m.id,
        'senderId': m.sender_id,
        'content': m.content,
        'timestamp': m.timestamp.isoformat()
    } for m in reversed(messages)]

    return jsonify({'messages': result}), 200

# 채팅 메시지 전송
@bp_chat.route('/<int:chatroomid>/messages', methods=['POST'])
@jwt_required()
def send_chatroom_message(chatroomid):
    from app import db
    user_id = int(get_jwt_identity())
    data = request.get_json()
    content = data.get('content')
    if not content:
        return jsonify({'message': '메시지 내용 누락'}), 400
    chatroom = Chatroom.query.get(chatroomid)
    if not chatroom:
        return jsonify({'message': '채팅방을 찾을 수 없습니다.'}), 404
    if user_id not in chatroom.participant_ids:
        return jsonify({'message': '메시지 전송 권한이 없습니다.'}), 403
    message = Message(
        chatroom_id=chatroomid,
        sender_id=user_id,
        content=content,
        timestamp=datetime.utcnow()
    )
    chatroom.last_message = content
    chatroom.updated_at = datetime.utcnow()
    db.session.add(message)
    db.session.commit()
    return jsonify({
        'messageId': message.id,
        'timestamp': message.timestamp.isoformat()
    }), 200

# 교환 약속 등록
@bp_chat.route('/trade-promise', methods=['POST'])
@jwt_required()
def register_trade_promise():
    from app import db
    user_id = int(get_jwt_identity())
    data = request.get_json()
    chatroom_id = data.get('chatroomId')
    date = data.get('date')
    title = data.get('title')
    location = data.get('location')
    if not all([chatroom_id, date, title, location]):
        return jsonify({'message': '필드 누락'}), 400
    chatroom = Chatroom.query.get(chatroom_id)
    if not chatroom:
        return jsonify({'message': '채팅방을 찾을 수 없습니다.'}), 404
    if user_id not in chatroom.participant_ids:
        return jsonify({'message': '약속 등록 권한이 없습니다.'}), 403
    
    try:
        # 만약 date_str 끝에 'Z'가 있으면 '+00:00'으로 변환
        if date.endswith('Z'):
            date = date[:-1] + '+00:00'
        promise_date = datetime.fromisoformat(date)
    except ValueError:
        return jsonify({'msg': '잘못된 날짜 형식입니다. ISO 8601 형식으로 보내주세요.'}), 400
    new_promise = TradePromise(
        chatroom_id=chatroom_id,
        creator_id=user_id,
        date=promise_date,
        title=title,
        location=location,
        created_at=datetime.utcnow()
    )
    db.session.add(new_promise)
    db.session.commit()
    return jsonify({
        'promiseId': new_promise.id,
        'chatroomId': new_promise.chatroom_id,
        'message': f"약속 '{title}'이(가) 등록되었습니다.",
        'createdAt': new_promise.created_at.isoformat()
    }), 201