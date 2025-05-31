from app import db
from datetime import datetime

# post.py
class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)  # 게시글 상세 설명
    category = db.Column(db.String(50), nullable=False)  # 카테고리
    thumbnail_image_url = db.Column(db.String(255), nullable=True)  # 썸네일 이미지 URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    author = db.relationship('User', back_populates='posts')
    trades = db.relationship('Trade', back_populates='post', lazy=True)

    def __repr__(self):
        return f'<Post id={self.id} title={self.title} user_id={self.user_id}>'
