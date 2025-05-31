from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User
from app.models.post import Post
from app.models.review import Review
from app.models.trade import Trade

user_bp = Blueprint('user', __name__, url_prefix='/api/v1/users')

# 회원가입
@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({"msg": "필수 입력 항목이 누락되었습니다."}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"msg": "이미 존재하는 사용자입니다."}), 409

    hashed_pw = generate_password_hash(password)
    user = User(username=username, email=email, password=hashed_pw)
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "회원가입 완료"}), 201

# 로그인
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"msg": "사용자 이름 또는 비밀번호가 올바르지 않습니다."}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200

# 로그아웃 (클라이언트에서 토큰 제거만으로 처리)
@user_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    return jsonify({"msg": f"User {user_id} logged out (토큰 클라이언트에서 제거 필요)"}), 200

# 프로필 조회
@user_bp.route('/<int:userid>/profile', methods=['GET'])
def user_profile(userid):
    user = User.query.get(userid)
    if not user:
        return jsonify({"msg": "사용자를 찾을 수 없습니다."}), 404

    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "profile_image_url": user.profile_image_url or "default.jpg",
            "registeredAt": user.created_at.strftime('%Y-%m-%d') if user.created_at else "",
            "current_points": user.points,
            "current_grade": user.grade or "보따리장수",
            "grade_icon_url": f"{user.grade.lower()}_grade.png",
            "total_trades": len(user.trades),
            "completed_trades": len([t for t in user.trades if t.status == 'COMPLETED']),
            "cancellation_count": 0,
            "cancellation_warning": "false"
        }
    })

# 리뷰 목록
@user_bp.route('/<int:userid>/reviews', methods=['GET'])
def user_review(userid):
    reviews = Review.query.filter_by(user_id=userid).order_by(Review.created_at.desc()).all()

    result = [{
        "review_id": r.id,
        "reviewer_id": r.reviewer_id,
        "rating": r.rating,
        "comment": r.comment,
        "date": r.created_at.strftime('%Y-%m-%d')
    } for r in reviews]

    return jsonify({
        "status": "success",
        "user_id": userid,
        "reviews": result
    }), 200

# 거래 이력
@user_bp.route('/<int:userid>/trades', methods=['GET'])
def user_trade_history(userid):
    trades = Trade.query.filter_by(requester_id=userid).order_by(Trade.created_at.desc()).all()

    result = [{
        "tradeId": t.id,
        "title": t.title,
        "status": t.status,
        "completedAt": t.completed_at.strftime('%Y-%m-%d') if t.completed_at else None
    } for t in trades]

    return jsonify(result), 200

# 포인트 수정
@user_bp.route('/<int:userid>/points', methods=['PATCH'])
@jwt_required()
def user_points(userid):
    if int(get_jwt_identity()) != userid:
        return jsonify({"msg": "권한이 없습니다."}), 403

    data = request.get_json()
    amount = data.get("amount")

    if amount is None:
        return jsonify({"msg": "필드 누락"}), 400

    user = User.query.get(userid)
    if not user:
        return jsonify({"msg": "사용자 없음"}), 404

    user.points += amount
    db.session.commit()

    return jsonify({"msg": "포인트 수정 성공"}), 200

# 등급 조회
@user_bp.route('/<int:userid>/grade', methods=['GET'])
def user_grade(userid):
    user = User.query.get(userid)

    if not user:
        return jsonify({"msg": "사용자 없음"}), 404

    if user.points >= 3000:
        grade = "교환장인"
    elif user.points >= 2000:
        grade = "장사꾼"
    elif user.points >= 1000:
        grade = "초보상인"
    else:
        grade = "보따리장수"

    return jsonify({
        "points": user.points,
        "grade": grade,
        "gradeIconUrl": f"{grade}_grade.png"
    }), 200

# 회원 탈퇴
@user_bp.route('/<int:userid>', methods=['DELETE'])
@jwt_required()
def delete_user(userid):
    if int(get_jwt_identity()) != userid:
        return jsonify({"msg": "권한이 없습니다."}), 403

    user = User.query.get(userid)
    if not user:
        return jsonify({"msg": "사용자 없음"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"msg": "회원 탈퇴 완료"}), 200
