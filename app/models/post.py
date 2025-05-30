from app import db  # SQLAlchemy 인스턴스 사용
from datetime import datetime  # 타임스탬프 생성

class Post(db.Model):  # 게시글 테이블 정의
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)  # 게시글 ID
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 작성자 ID (users.id 참조)
    title = db.Column(db.String(255), nullable=False)  # 게시글 제목
    description = db.Column(db.Text, nullable=False)  # 게시글 상세 설명
    category = db.Column(db.String(50), nullable=False)  # 카테고리
    thumbnail_image_url = db.Column(db.String(255), nullable=True)  # 썸네일 이미지 URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 작성 시각

    # 관계 설정
    author = db.relationship('User', backref=db.backref('posts', lazy=True))  # 작성자(User)와 연결
    trades = db.relationship('Trade', backref='post', lazy=True)  # 관련 거래 목록

    def __repr__(self):  # 디버깅용 출력 형식
        return f'<Post id={self.id} title={self.title} author_id={self.author_id}>'
