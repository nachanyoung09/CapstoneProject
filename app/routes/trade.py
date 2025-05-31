from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.trade import Trade, TradeStatus  # TradeStatus import 필요
from app.models.review import Review
from datetime import datetime

bp_trade = Blueprint('trade', __name__, url_prefix='/api/v1/trades')

# 거래 수락
@bp_trade.route('/<int:tradeid>/accept', methods=['POST'])
@jwt_required()
def accept_trade(tradeid):
    trade = Trade.query.get(tradeid)
    if not trade:
        return jsonify({'msg': '해당 거래 제안을 찾을 수 없습니다.'}), 404

    user_id = int(get_jwt_identity())
    if trade.receiver_id != user_id:
        return jsonify({'msg': '수락 권한이 없습니다.'}), 403

    trade.status = TradeStatus.ACCEPTED
    trade.accepted_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Trade accepted successfully."}), 200

# 거래 완료 처리
@bp_trade.route('/<int:tradeid>/complete', methods=['POST'])
@jwt_required()
def complete_trade(tradeid):
    trade = Trade.query.get(tradeid)
    if not trade:
        return jsonify({'msg': '해당 거래 제안을 찾을 수 없습니다.'}), 404

    user_id = int(get_jwt_identity())
    if trade.receiver_id != user_id and trade.requester_id != user_id:
        return jsonify({'msg': '완료 권한이 없습니다.'}), 403

    trade.status = TradeStatus.COMPLETED
    trade.completed_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"status": trade.status.value}), 200

# 거래 리뷰 등록
@bp_trade.route('/<int:tradeid>/review', methods=['POST'])
@jwt_required()
def review_trade(tradeid):
    trade = Trade.query.get(tradeid)
    if not trade:
        return jsonify({'msg': '해당 거래 제안을 찾을 수 없습니다.'}), 404

    user_id = int(get_jwt_identity())
    data = request.get_json()
    rating = data.get("rating")
    comment = data.get("comment")

    if not all([rating, comment]):
        return jsonify({"msg": "잘못된 입력"}), 400

    new_review = Review(
        trade_id=trade.id,
        reviewer_id=user_id,
        user_id=trade.receiver_id if user_id == trade.requester_id else trade.requester_id,
        rating=rating,
        comment=comment
    )
    db.session.add(new_review)
    db.session.commit()

    return jsonify({"review_id": new_review.id}), 200
