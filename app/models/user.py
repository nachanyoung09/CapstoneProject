from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    profile_image_url = db.Column(db.String(255), nullable=True)
    points = db.Column(db.Integer, default=0)
    grade = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 게시글 작성자 관계
    posts = db.relationship('Post', backref='author', lazy=True)
    # 거래 관계
    requested_trades = db.relationship('Trade', backref='requester', lazy=True, foreign_keys='Trade.requester_id')
    received_trades = db.relationship('Trade', backref='receiver', lazy=True, foreign_keys='Trade.receiver_id')
    @property
    def trades(self):
        # 요청 및 수락된 거래 모두 포함
        return self.requested_trades + self.received_trades

    # 리뷰 관계
    reviews_written = db.relationship('Review', backref='reviewer', lazy=True, foreign_keys='Review.reviewer_id')
    reviews_received = db.relationship('Review', backref='target_user', lazy=True, foreign_keys='Review.user_id')

    # 가치 평가 관계
    valuation_posts = db.relationship('ValuationPost', backref='author', lazy=True)
    valuation_opinions = db.relationship('ValuationOpinion', backref='user', lazy=True)

    # 분석 데이터 1:1 관계
    analytics = db.relationship('Analytics', backref=db.backref('user', uselist=False))

    # 채팅 및 약속 관계
    messages = db.relationship('Message', backref='sender', lazy=True)
    trade_promises = db.relationship('TradePromise', backref='creator', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'