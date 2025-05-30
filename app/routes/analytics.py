from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.user import User
from app.models.trade import Trade
from app.models.review import Review
from app.models.analytic import Analytics  # 추가된 모델
from sqlalchemy import func
from datetime import datetime

bp_analytics = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

# 사용자 거래 및 평점 분석 조회 + DB 저장
@bp_analytics.route('/user/<int:userid>', methods=['GET'])
@jwt_required()
def analyze_user(userid):
    user = User.query.get(userid)
    if not user:
        return jsonify({"msg": "사용자를 찾을 수 없습니다."}), 404

    trades = Trade.query.filter(
        (Trade.requester_id == userid) | (Trade.receiver_id == userid)
    ).all()

    if not trades:
        return jsonify({"msg": "거래 내역이 없습니다."}), 404

    total_trades = len(trades)
    successful_trades = len([t for t in trades if t.status == 'COMPLETED'])
    success_rate = round((successful_trades / total_trades) * 100, 2)

    reviews = Review.query.filter_by(user_id=userid).all()
    average_rating = round(sum(r.rating for r in reviews) / len(reviews), 2) if reviews else 0

    monthly_trade_counts = db.session.query(
        func.date_format(Trade.completed_at, "%Y-%m"),
        func.count()
    ).filter(
        ((Trade.requester_id == userid) | (Trade.receiver_id == userid)) &
        (Trade.status == 'COMPLETED')
    ).group_by(
        func.date_format(Trade.completed_at, "%Y-%m")
    ).all()

    monthly_average_ratings = db.session.query(
        func.date_format(Review.created_at, "%Y-%m"),
        func.avg(Review.rating)
    ).filter_by(user_id=userid).group_by(
        func.date_format(Review.created_at, "%Y-%m")
    ).all()

    # 분석 결과 DB에 저장 또는 업데이트
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

# 거래 분석 수동 업데이트 (관리자용)
@bp_analytics.route('/user/<int:userid>', methods=['PUT'])
@jwt_required()
def analyze_update(userid):
    user = User.query.get(userid)
    if not user:
        return jsonify({"msg": "사용자를 찾을 수 없습니다."}), 404

    data = request.get_json()
    totalTrades = data.get("totalTrades")
    successfulTrades = data.get("successfulTrades")
    averageRating = data.get("averageRating")

    if not all([totalTrades is not None, successfulTrades is not None, averageRating is not None]):
        return jsonify({"msg": "필수 항목 누락"}), 400

    analytics = Analytics.query.filter_by(user_id=userid).first()
    if not analytics:
        analytics = Analytics(user_id=userid)
        db.session.add(analytics)

    analytics.total_trades = totalTrades
    analytics.successful_trades = successfulTrades
    analytics.success_rate = round((successfulTrades / totalTrades) * 100, 2)
    analytics.average_rating = averageRating
    analytics.last_updated = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "msg": "거래 데이터 수동 업데이트 완료",
        "userId": userid,
        "totalTrades": totalTrades,
        "successfulTrades": successfulTrades,
        "averageRating": averageRating
    }), 200
