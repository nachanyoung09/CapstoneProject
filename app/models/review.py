# app/models/review.py
from app import db
from datetime import datetime


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trades.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 리뷰 대상자
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    trade = db.relationship('Trade', back_populates='review', lazy=True)
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], back_populates='reviews_written', lazy=True)
    user = db.relationship('User', foreign_keys=[user_id], back_populates='reviews_received', lazy=True)

    def __repr__(self):
        return f"<Review id={self.id} trade_id={self.trade_id} reviewer={self.reviewer_id} user={self.user_id} rating={self.rating}>"