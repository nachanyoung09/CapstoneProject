from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.valuation_post import ValuationPost
from app.models.valuation_opinion import ValuationOpinion
from datetime import datetime

bp_valuation = Blueprint('valuation', __name__, url_prefix='/api/v1/valuations')

# GET: 가치 평가 게시글 목록 조회 (페이지네이션 + 카테고리 필터)
@bp_valuation.route('', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_valuation_posts():
    # 쿼리 파라미터
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    category = request.args.get('category', type=str)

    # 기본 쿼리
    query = ValuationPost.query
    if category:
        query = query.filter_by(category=category)

    # 페이지네이션 및 정렬
    pagination = query.order_by(ValuationPost.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    posts = []
    for post in pagination.items:
        # 평균 가격 계산
        opinions = [op.price for op in post.opinions if op.price is not None]
        avg_price = sum(opinions) / len(opinions) if opinions else 0
        posts.append({
            'postId': post.id,
            'title': post.title,
            'averagePrice': avg_price,
            'createdAt': post.created_at.strftime('%Y-%m-%d %H:%M')
        })

    return jsonify({
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'posts': posts
    }), 200

# POST: 가치 평가 게시글 작성
@bp_valuation.route('', methods=['POST'], strict_slashes=False)
@jwt_required()
def create_valuation_post():
    data = request.get_json() or {}
    title = data.get('title')
    description = data.get('description')
    category = data.get('category')
    user_id = int(get_jwt_identity())

    if not title or not description or not category:
        return jsonify({'msg': 'title, description, category 필수'}), 400

    new_post = ValuationPost(
        title=title,
        description=description,
        category=category,
        user_id=user_id,
        created_at=datetime.utcnow()
    )
    db.session.add(new_post)
    db.session.commit()

    return jsonify({
        'postId': new_post.id,
        'title': new_post.title,
        'description': new_post.description,
        'category': new_post.category,
        'createdAt': new_post.created_at.strftime('%Y-%m-%d %H:%M')
    }), 201

# GET: 가치 평가 게시글 상세 조회
@bp_valuation.route('/<int:postid>', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_valuation_post(postid):
    post = ValuationPost.query.get(postid)
    if not post:
        return jsonify({'msg': '게시글을 찾을 수 없습니다.'}), 404

    # 평균 가격 및 총 평가 수
    opinions = [op.price for op in post.opinions if op.price is not None]
    avg_price = sum(opinions) / len(opinions) if opinions else 0
    total_evaluations = len(opinions)

    return jsonify({
        'postId': post.id,
        'title': post.title,
        'description': post.description,
        'category': post.category,
        'averagePrice': avg_price,
        'totalEvaluations': total_evaluations,
        'createdAt': post.created_at.strftime('%Y-%m-%d %H:%M')
    }), 200

# DELETE: 가치 평가 게시글 삭제
@bp_valuation.route('/<int:postid>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
def delete_valuation_post(postid):
    post = ValuationPost.query.get(postid)
    if not post:
        return jsonify({'msg': '게시글을 찾을 수 없습니다.'}), 404

    current_user = int(get_jwt_identity())
    if post.user_id != current_user:
        return jsonify({'msg': '권한이 없습니다.'}), 403

    db.session.delete(post)
    db.session.commit()
    return jsonify({'msg': '게시글 삭제 성공'}), 200

# POST: 평가 의견 등록
@bp_valuation.route('/<int:postid>/price', methods=['POST'], strict_slashes=False)
@jwt_required()
def create_valuation_opinion(postid):
    post = ValuationPost.query.get(postid)
    if not post:
        return jsonify({'msg': '게시글을 찾을 수 없습니다.'}), 404

    data = request.get_json() or {}
    price = data.get('price')
    user_id = int(get_jwt_identity())

    if price is None:
        return jsonify({'msg': 'price 필수'}), 400

    # 중복 평가 방지 (선택 사항, 필요 시 해제)
    existing = ValuationOpinion.query.filter_by(post_id=postid, user_id=user_id).first()
    if existing:
        return jsonify({'msg': '이미 평가한 게시글입니다.'}), 400

    new_opinion = ValuationOpinion(
        post_id=postid,
        user_id=user_id,
        price=price,
        created_at=datetime.utcnow()
    )
    db.session.add(new_opinion)
    db.session.commit()

    return jsonify({'msg': '의견 등록 성공'}), 201

# GET: 게시글의 평균 가격 조회
@bp_valuation.route('/<int:postid>/average', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_valuation_average(postid):
    post = ValuationPost.query.get(postid)
    if not post:
        return jsonify({'msg': '게시글을 찾을 수 없습니다.'}), 404

    opinions = [op.price for op in post.opinions if op.price is not None]
    valid_count = len(opinions)
    avg_price = sum(opinions) / valid_count if valid_count else 0

    return jsonify({
        'postId': post.id,
        'validCount': valid_count,
        'averagePrice': avg_price
    }), 200
