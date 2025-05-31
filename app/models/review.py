from app import db
from datetime import datetime
# review.py
class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trades.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviewer = db.relationship(
        'User', foreign_keys=[reviewer_id], back_populates='reviews_written'
    )
    target_user = db.relationship(
        'User', foreign_keys=[user_id], back_populates='reviews_received'
    )
    trade = db.relationship('Trade', back_populates='reviews')

    def __repr__(self):
        return f'<Review user_id={self.user_id} rating={self.rating}>'