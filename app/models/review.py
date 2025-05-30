from app import db  # SQLAlchemy 인스턴스 사용
from datetime import datetime  # 생성일자 처리

class Review(db.Model):  # 리뷰 테이블 정의
    __tablename__ = 'reviews'  # 테이블 이름 지정

    id = db.Column(db.Integer, primary_key=True)  # 리뷰 ID (기본키)
    trade_id = db.Column(db.Integer, db.ForeignKey('trades.id'), nullable=False)  # 연결된 거래 ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 리뷰 대상자
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 리뷰 작성자
    rating = db.Column(db.Integer, nullable=False)  # 평점 (1~5점 예상)
    comment = db.Column(db.Text, nullable=True)  # 자유 코멘트
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 작성 시각

    # 관계 설정
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviews_written')  # 작성자와 연결
    target_user = db.relationship('User', foreign_keys=[user_id], backref='reviews_received')  # 대상자와 연결
    trade = db.relationship('Trade', backref='reviews')  # 연결된 거래 객체

    def __repr__(self):  # 디버깅용 출력
        return f'<Review user_id={self.user_id} rating={self.rating}>'
