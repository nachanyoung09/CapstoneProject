# app/routes/trade_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.trade import Trade, TradeStatus
from app.models.review import Review
from app.models.user import User
from app.models.post import Post  # Post 모델 임포트
from datetime import datetime

bp_trade = Blueprint('trade', __name__, url_prefix='/api/v1/trades')

# ──[1] 거래 제안 생성 (예시: 채팅 페이지에서 양쪽 동의 시 호출)────────
@bp_trade.route('', methods=['POST'], strict_slashes=False)
@jwt_required()
def create_trade():
    """
    거래 제안을 만듭니다. (채팅에서 약속이 성사된 후 호출)
    request JSON:
      {
        "post_id": <int>,       # 거래할 게시글 ID
        "receiver_id": <int>,   # 상대방 user ID
        "message": <string>     # (선택) 거래 제안 메시지
      }
    응답(201):
      {
        "trade_id": <int>,
        "status": "PENDING",
        "created_at": "<YYYY-MM-DD HH:MM>"
      }
    오류:
      400: 필수 필드 누락
      403: 자신과 거래 제안 시도
      404: post_id 또는 receiver_id에 해당하는 레코드 없음
    """
    data = request.get_json() or {}
    post_id = data.get('post_id')
    receiver_id = data.get('receiver_id')
    message = data.get('message', None)
    requester_id = int(get_jwt_identity())

    # 1) 필수값 확인
    if post_id is None or receiver_id is None:
        return jsonify({"msg": "post_id와 receiver_id가 필요합니다."}), 400

    # 2) 자신에게 거래 제안 불가
    if receiver_id == requester_id:
        return jsonify({"msg": "자신에게 거래 제안할 수 없습니다."}), 403

    # 3) post_id가 실제로 존재하는지 확인
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"msg": "거래할 게시글이 존재하지 않습니다."}), 404

    # 4) receiver_id가 실제 사용자로 존재하는지 확인
    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({"msg": "수신자(사용자)가 존재하지 않습니다."}), 404

    # 모든 검증 통과 시에만 새 Trade 생성
    new_trade = Trade(
        post_id=post_id,
        requester_id=requester_id,
        receiver_id=receiver_id,
        message=message,
        status=TradeStatus.PENDING,
        created_at=datetime.utcnow()
    )
    db.session.add(new_trade)
    db.session.commit()

    return jsonify({
        "trade_id": new_trade.id,
        "status": new_trade.status.value,
        "created_at": new_trade.created_at.strftime('%Y-%m-%d %H:%M')
    }), 201


# ──[2] 거래 수락───────────────────────────────────────────────────────
@bp_trade.route('/<int:tradeid>/accept', methods=['POST'], strict_slashes=False)
@jwt_required()
def accept_trade(tradeid):
    """
    PENDING 상태의 거래 제안을 수락합니다.
    Path Parameter: tradeid (int)
    응답(200):
      {
        "message": "Trade accepted successfully."
      }
    오류:
      403: 권한 없음 (receiver만 수락 가능)
      404: 거래 없음
      400: 이미 ACCEPTED 혹은 COMPLETED 상태인 경우
    """
    trade = Trade.query.get(tradeid)
    if not trade:
        return jsonify({'msg': '해당 거래 제안을 찾을 수 없습니다.'}), 404

    user_id = int(get_jwt_identity())
    # 권한 확인: 오직 receiver_id만 수락 가능
    if trade.receiver_id != user_id:
        return jsonify({'msg': '수락 권한이 없습니다.'}), 403

    # 현재 상태가 PENDING이어야 함
    if trade.status != TradeStatus.PENDING:
        return jsonify({'msg': '현재 상태에서 수락할 수 없습니다.'}), 400

    trade.status = TradeStatus.ACCEPTED
    trade.accepted_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Trade accepted successfully."}), 200


# ──[3] 거래 완료 처리───────────────────────────────────────────────────
@bp_trade.route('/<int:tradeid>/complete', methods=['POST'], strict_slashes=False)
@jwt_required()
def complete_trade(tradeid):
    """
    ACCEPTED 상태의 거래를 완료 처리합니다.
    Path Parameter: tradeid (int)
    응답(200):
      {
        "status": "COMPLETED"
      }
    오류:
      403: 권한 없음 (requester 또는 receiver만 가능)
      404: 거래 없음
      400: 현재 상태가 COMPLETED가 아닌 경우
    """
    trade = Trade.query.get(tradeid)
    if not trade:
        return jsonify({'msg': '해당 거래 제안을 찾을 수 없습니다.'}), 404

    user_id = int(get_jwt_identity())
    # 권한 확인: requester 또는 receiver만 가능
    if trade.requester_id != user_id and trade.receiver_id != user_id:
        return jsonify({'msg': '완료 권한이 없습니다.'}), 403

    # 현재 상태가 ACCEPTED이어야만 완료 가능
    if trade.status != TradeStatus.ACCEPTED:
        return jsonify({'msg': '현재 상태에서 완료할 수 없습니다.'}), 400

    trade.status = TradeStatus.COMPLETED
    trade.completed_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"status": trade.status.value}), 200


# ──[4] 거래 리뷰 등록────────────────────────────────────────────────────
@bp_trade.route('/<int:tradeid>/review', methods=['POST'], strict_slashes=False)
@jwt_required()
def review_trade(tradeid):
    """
    COMPLETED 상태의 거래에 대해 리뷰를 작성합니다.
    Path Parameter: tradeid (int)
    requestBody:
      {
        "rating": <int>,     # 평점 (1~5 등)
        "comment": <string>  # 리뷰 코멘트
      }
    응답(200):
      {
        "review_id": <int>
      }
    오류:
      400: 잘못된 입력 (rating 또는 comment 누락)
      403: 권한 없음 (거래 완료 후 참여자만 작성 가능)
      404: 거래 없음
      400: 현재 상태가 COMPLETED가 아닌 경우
    """
    trade = Trade.query.get(tradeid)
    if not trade:
        return jsonify({'msg': '해당 거래 제안을 찾을 수 없습니다.'}), 404

    # 거래 상태가 COMPLETED여야 리뷰 작성 가능
    if trade.status != TradeStatus.COMPLETED:
        return jsonify({'msg': '거래가 완료된 후 리뷰를 작성할 수 있습니다.'}), 400

    user_id = int(get_jwt_identity())
    # 권한 확인: 거래 참여자(requester 또는 receiver)만 리뷰 작성 가능
    if trade.requester_id != user_id and trade.receiver_id != user_id:
        return jsonify({'msg': '리뷰 작성 권한이 없습니다.'}), 403

    data = request.get_json() or {}
    rating = data.get("rating")
    comment = data.get("comment")

    if rating is None or comment is None:
        return jsonify({"msg": "rating과 comment가 모두 필요합니다."}), 400

    # 이미 동일 거래에 리뷰를 작성했는지 확인 (중복 방지)
    existing = Review.query.filter_by(trade_id=tradeid, reviewer_id=user_id).first()
    if existing:
        return jsonify({'msg': '이미 리뷰를 작성하셨습니다.'}), 400

    # 상대방 user_id 설정: reviewer_id가 현재 user_id, user_id는 리뷰 대상자
    target_user_id = trade.receiver_id if user_id == trade.requester_id else trade.requester_id

    new_review = Review(
        trade_id=trade.id,
        reviewer_id=user_id,
        user_id=target_user_id,
        rating=rating,
        comment=comment,
        created_at=datetime.utcnow()
    )
    db.session.add(new_review)
    db.session.commit()

    return jsonify({"review_id": new_review.id}), 200
