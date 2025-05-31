import enum
from app import db  # SQLAlchemy 인스턴스 사용
from datetime import datetime  # 타임스탬프 생성에 사용

class TradeStatus(enum.Enum):  # 거래 상태를 위한 Enum 클래스
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"
# trade.py
class Trade(db.Model):
    __tablename__ = 'trades'

    id = db.Column(db.Integer, primary_key=True)  # 거래 ID (기본키)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)  # 거래 관련 게시글 ID
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 거래 요청자 ID
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 거래 수락자 ID
    message = db.Column(db.Text, nullable=True)  # 거래 제안 메시지
    status = db.Column(db.Enum(TradeStatus), default=TradeStatus.PENDING, nullable=False)  # 거래 상태 Enum 필드
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 거래 생성 시각
    accepted_at = db.Column(db.DateTime, nullable=True)  # 거래 수락 시각
    completed_at = db.Column(db.DateTime, nullable=True)  # 거래 완료 시각

    requester = db.relationship(
        'User', foreign_keys=[requester_id], back_populates='requested_trades'
    )
    receiver = db.relationship(
        'User', foreign_keys=[receiver_id], back_populates='received_trades'
    )
    post = db.relationship(
        'Post', foreign_keys=[post_id], back_populates='trades'
    )
    reviews = db.relationship('Review', back_populates='trade', lazy=True)

    #trade_promise = db.relationship(
    #    'TradePromise', back_populates='trade', uselist=False
    #)

    def __repr__(self):
        return f'<Trade id={self.id} post_id={self.post_id} status={self.status.value}>'