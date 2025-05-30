from app import db
from datetime import datetime

class ValuationPost(db.Model):
    __tablename__ = 'valuation_posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)        # renamed
    category = db.Column(db.String(50), nullable=False)      # non-nullable
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship('User', backref='valuation_posts')
    opinions = db.relationship('ValuationOpinion', backref='post', lazy=True)

    def get_average_price(self):
        prices = [op.price for op in self.opinions if op.price is not None]
        return round(sum(prices) / len(prices), 2) if prices else 0

    def __repr__(self):
        return f'<ValuationPost id={self.id} title={self.title}>'
