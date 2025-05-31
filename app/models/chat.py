# app/models/chat.py
from app import db
from datetime import datetime

class Chatroom(db.Model):
    __tablename__ = 'chatrooms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    participant_ids = db.Column(db.JSON, nullable=False)  # JSON으로 리스트 저장
    related_post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    last_message = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    messages = db.relationship('Message', back_populates='chatroom', lazy=True)
    trade_promises = db.relationship('TradePromise', back_populates='chatroom', lazy=True)

    def __repr__(self):
        return f"<Chatroom {self.name} participants={self.participant_ids}>"


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chatrooms.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    chatroom = db.relationship('Chatroom', back_populates='messages')
    sender = db.relationship('User', back_populates='messages')
    def __repr__(self):
        return f"<Message from={self.sender_id} in room={self.chatroom_id}>"


class TradePromise(db.Model):
    __tablename__ = 'trade_promises'

    id = db.Column(db.Integer, primary_key=True)
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chatrooms.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 약속 생성자
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 관계 설정
    chatroom = db.relationship('Chatroom', back_populates='trade_promises')
    creator = db.relationship('User', back_populates='trade_promises')

    def __repr__(self):
        return f"<TradePromise {self.title} at {self.location} on {self.date}>"
