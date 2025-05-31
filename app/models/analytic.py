from app import db
from datetime import datetime

class Analytics(db.Model):
    __tablename__ = 'analytics'

    id = db.Column(db.Integer, primary_key=True)  # 고유 식별자
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)  # 유저 ID (1:1 관계 유지)
    total_trades = db.Column(db.Integer, nullable=False, default=0)  # 총 거래 수
    successful_trades = db.Column(db.Integer, nullable=False, default=0)  # 성공 거래 수
    success_rate = db.Column(db.Float, nullable=False, default=0.0)  # 성공 비율 (퍼센트)
    average_rating = db.Column(db.Float, nullable=False, default=0.0)  # 평균 평점
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 마지막 업데이트 시각

    # User 모델과 1:1 관계
    user = db.relationship('User', back_populates='analytics', uselist=False)

    def __repr__(self):
        return f"<Analytics user_id={self.user_id} trades={self.total_trades} success={self.success_rate}% rating={self.average_rating}>"
