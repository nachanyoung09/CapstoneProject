# app/models/trade.py
from app import db
from datetime import datetime
import enum


class TradeStatus(enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"


class Trade(db.Model):
    __tablename__ = 'trades'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(TradeStatus), nullable=False, default=TradeStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    post = db.relationship('Post', back_populates='trades', lazy=True)
    requester = db.relationship('User', foreign_keys=[requester_id], back_populates='requested_trades', lazy=True)
    receiver = db.relationship('User', foreign_keys=[receiver_id], back_populates='received_trades', lazy=True)
    review = db.relationship('Review', back_populates='trade', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Trade id={self.id} status={self.status.value} post_id={self.post_id}>"