# app/models/valuation_post.py
from app import db
from datetime import datetime

class ValuationPost(db.Model):
    __tablename__ = 'valuation_posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: User (author) and Opinions
    author = db.relationship('User', back_populates='valuation_posts')
    opinions = db.relationship('ValuationOpinion', back_populates='post', lazy=True, cascade='all, delete-orphan')

    def get_average_price(self):
        """
        게시글에 연결된 모든 ValuationOpinion을 기반으로 평균 가격 계산
        """
        prices = [op.price for op in self.opinions if op.price is not None]
        if not prices:
            return 0
        return round(sum(prices) / len(prices), 2)

    def get_total_evaluations(self):
        """
        유효한 가격 평가 수 반환
        """
        return len([op for op in self.opinions if op.price is not None])

    def __repr__(self):
        return f"<ValuationPost id={self.id} title={self.title}>"
