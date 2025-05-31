from app import db
from datetime import datetime

# user.py
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    profile_image_url = db.Column(db.String(255), nullable=True)
    points = db.Column(db.Integer, default=0)
    grade = db.Column(db.String(20), nullable=False,default='보따리장수')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship('Post', back_populates='author', lazy=True)
    requested_trades = db.relationship(
        'Trade', back_populates='requester', lazy=True,
        foreign_keys='Trade.requester_id'
    )
    received_trades = db.relationship(
        'Trade', back_populates='receiver', lazy=True,
        foreign_keys='Trade.receiver_id'
    )

    @property
    def trades(self):
        return self.requested_trades + self.received_trades

    reviews_written = db.relationship(
        'Review', back_populates='reviewer', lazy=True,
        foreign_keys='Review.reviewer_id'
    )
    reviews_received = db.relationship(
        'Review', back_populates='target_user', lazy=True,
        foreign_keys='Review.user_id'
    )

    valuation_posts = db.relationship(
        'ValuationPost', back_populates='author', lazy=True
    )
    valuation_opinions = db.relationship(
        'ValuationOpinion', back_populates='user', lazy=True
    )

    analytics = db.relationship(
        'Analytics', back_populates='user', uselist=False
    )

    messages = db.relationship('Message', back_populates='sender', lazy=True)
    trade_promises = db.relationship('TradePromise', back_populates='creator', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'