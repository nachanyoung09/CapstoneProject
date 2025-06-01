# app/models/analytics.py
from app import db
from datetime import datetime

class Analytics(db.Model):
    __tablename__ = 'analytics'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    total_trades = db.Column(db.Integer, nullable=False, default=0)
    successful_trades = db.Column(db.Integer, nullable=False, default=0)
    success_rate = db.Column(db.Float, nullable=False, default=0.0)
    average_rating = db.Column(db.Float, nullable=False, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 1:1 관계 - User 모델과 연결
    user = db.relationship('User', back_populates='analytics', uselist=False)

    def __repr__(self):
        return f"<Analytics user_id={self.user_id} total_trades={self.total_trades} success_rate={self.success_rate}>"
