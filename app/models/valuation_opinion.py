# app/models/valuation_opinion.py
from app import db
from datetime import datetime

class ValuationOpinion(db.Model):
    __tablename__ = 'valuation_opinions'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('valuation_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: Post and User
    post = db.relationship('ValuationPost', back_populates='opinions', lazy=True)
    user = db.relationship('User', back_populates='valuation_opinions', lazy=True)

    def __repr__(self):
        return f"<ValuationOpinion post_id={self.post_id} user_id={self.user_id} price={self.price}>"