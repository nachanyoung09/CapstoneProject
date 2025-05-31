from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.valuation_post import ValuationPost
from app.models.valuation_opinion import ValuationOpinion

from datetime import datetime

bp_valuation = Blueprint('valuation', __name__, url_prefix='/api/v1/valuations')

# 전체 가치 평가 게시글 목록
@bp_valuation.route('', methods=['GET'])
@jwt_required()
def view_valuation():
    category = request.args.get("category")
    query = ValuationPost.query
    if category:
        query = query.filter_by(category=category)
    posts = query.order_by(ValuationPost.created_at.desc()).all()

    result = [{
        "postId": post.id,
        "title": post.title,
        "averagePrice": post.get_average_price(),
        "createdAt": post.created_at.strftime('%Y-%m-%d %H:%M')
    } for post in posts]

    return jsonify(result), 200

# 가치 평가 게시글 등록
@bp_valuation.route('', methods=['POST'])
@jwt_required()
def post_valuation():
    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    category = data.get("category")

    if not all([title, description, category]):
        return jsonify({"msg": "필수 필드 누락"}), 400

    user_id = int(get_jwt_identity())
    post = ValuationPost(
        title=title,
        description=description,
        category=category,
        user_id=user_id
    )
    db.session.add(post)
    db.session.commit()

    return jsonify({"postId": post.id}), 201

# 게시글 상세 조회
@bp_valuation.route('/<int:postid>', methods=['GET'])
@jwt_required()
def view_valuation_detail(postid):
    post = ValuationPost.query.get(postid)
    if not post:
        return jsonify({"msg": "게시글을 찾을 수 없습니다."}), 404

    return jsonify({
        "postId": post.id,
        "title": post.title,
        "description": post.description,
        "averagePrice": post.get_average_price(),
        "totalEvaluations": len(post.opinions),
        "createdAt": post.created_at.strftime('%Y-%m-%d %H:%M')
    }), 200

# 가격 평가 등록
@bp_valuation.route('/<int:postid>/price', methods=['POST'])
@jwt_required()
def valuation_price(postid):
    post = ValuationPost.query.get(postid)
    if not post:
        return jsonify({"msg": "게시글을 찾을 수 없습니다."}), 404

    data = request.get_json()
    price = data.get("price")
    if not price:
        return jsonify({"msg": "가격 누락"}), 400

    user_id = int(get_jwt_identity())
    opinion = ValuationOpinion(
        post_id=postid,
        user_id=user_id,
        price=price
    )
    db.session.add(opinion)
    db.session.commit()

    return jsonify({"msg": "평가 등록 완료"}), 200

# 평균 가격 조회
@bp_valuation.route('/<int:postid>/average', methods=['GET'])
@jwt_required()
def valuation_average(postid):
    post = ValuationPost.query.get(postid)
    if not post:
        return jsonify({"msg": "게시글을 찾을 수 없습니다."}), 404

    valid_opinions = [op.price for op in post.opinions if op.price is not None]
    avg_price = sum(valid_opinions) / len(valid_opinions) if valid_opinions else 0

    return jsonify({
        "postId": post.id,
        "validCount": len(valid_opinions),
        "averagePrice": avg_price
    }), 200
