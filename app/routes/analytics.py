# app/routes/analytics_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.analytic import Analytics
from app.models.trade import Trade, TradeStatus
from app.models.review import Review
from app.models.user import User
from datetime import datetime
from sqlalchemy import func

bp_analytics = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

# GET: 특정 사용자 거래 및 평점 통계 조회 (생성 또는 업데이트)
@bp_analytics.route('/user/<int:userid>', methods=['GET'], strict_slashes=False)
@jwt_required()
def analyze_user(userid):
    # 사용자 존재 확인
    user = User.query.get(userid)
    if not user:
        return jsonify({"msg": "사용자를 찾을 수 없습니다."}), 404

    # 해당 사용자의 모든 거래 조회
    trades = Trade.query.filter(
        (Trade.requester_id == userid) | (Trade.receiver_id == userid)
    ).all()

    # 거래 내역이 없으면 빈 통계 반환 (404 대신)
    if not trades:
        return jsonify({
            "userId": userid,
            "totalTrades": 0,
            "successfulTrades": 0,
            "successRate": 0,
            "averageRating": 0,
            "monthlyTradeCounts": [],
            "monthlyAverageRatings": []
        }), 200

    total_trades = len(trades)
    # TradeStatus enum 비교로 수정
    successful_trades = len([t for t in trades if t.status == TradeStatus.COMPLETED])
    # 성공률 계산, 총 거래 수 보호
    if total_trades > 0:
        success_rate = round((successful_trades / total_trades) * 100, 2)
    else:
        success_rate = 0

    # 리뷰 평점 계산
    reviews = Review.query.filter_by(user_id=userid).all()
    if reviews:
        average_rating = round(sum(r.rating for r in reviews) / len(reviews), 2)
    else:
        average_rating = 0

    # 월별 완료된 거래 건수 조회 (MySQL용 date_format 사용)
    monthly_trade_counts = db.session.query(
        func.date_format(Trade.completed_at, "%Y-%m"),
        func.count()
    ).filter(
        ((Trade.requester_id == userid) | (Trade.receiver_id == userid)) &
        (Trade.status == TradeStatus.COMPLETED)
    ).group_by(
        func.date_format(Trade.completed_at, "%Y-%m")
    ).all()

    # 월별 평균 평점 조회
    monthly_average_ratings = db.session.query(
        func.date_format(Review.created_at, "%Y-%m"),
        func.avg(Review.rating)
    ).filter_by(user_id=userid).group_by(
        func.date_format(Review.created_at, "%Y-%m")
    ).all()

    # Analytics 테이블에 기록
    analytics = Analytics.query.filter_by(user_id=userid).first()
    if not analytics:
        analytics = Analytics(user_id=userid)
        db.session.add(analytics)

    analytics.total_trades = total_trades
    analytics.successful_trades = successful_trades
    analytics.success_rate = success_rate
    analytics.average_rating = average_rating
    analytics.last_updated = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "userId": userid,
        "totalTrades": total_trades,
        "successfulTrades": successful_trades,
        "successRate": success_rate,
        "averageRating": average_rating,
        "monthlyTradeCounts": [
            {"month": m, "count": c} for m, c in monthly_trade_counts
        ],
        "monthlyAverageRatings": [
            {"month": m, "averageRating": round(r, 2)} for m, r in monthly_average_ratings
        ]
    }), 200

# PUT: 특정 사용자 거래 통계 수동 업데이트
@bp_analytics.route('/user/<int:userid>', methods=['PUT'], strict_slashes=False)
@jwt_required()
def analyze_update(userid):
    # 사용자 존재 확인
    user = User.query.get(userid)
    if not user:
        return jsonify({"msg": "사용자를 찾을 수 없습니다."}), 404

    data = request.get_json() or {}
    total_trades = data.get("totalTrades")
    successful_trades = data.get("successfulTrades")
    average_rating = data.get("averageRating")

    if total_trades is None or successful_trades is None or average_rating is None:
        return jsonify({"msg": "필수 항목 누락"}), 400

    # ZeroDivisionError 방지
    if total_trades == 0:
        success_rate = 0
    else:
        success_rate = round((successful_trades / total_trades) * 100, 2)

    analytics = Analytics.query.filter_by(user_id=userid).first()
    if not analytics:
        analytics = Analytics(user_id=userid)
        db.session.add(analytics)

    analytics.total_trades = total_trades
    analytics.successful_trades = successful_trades
    analytics.success_rate = success_rate
    analytics.average_rating = average_rating
    analytics.last_updated = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "msg": "거래 데이터 수동 업데이트 완료",
        "userId": userid,
        "totalTrades": total_trades,
        "successfulTrades": successful_trades,
        "averageRating": average_rating
    }), 200
