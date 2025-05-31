
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.post import Post
from datetime import datetime

bp_post = Blueprint('post', __name__, url_prefix='/api/v1/posts')

# 게시글 등록
@bp_post.route('', methods=['POST'])
@jwt_required()
def register_post():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    category = data.get('category')
    thumbnail = data.get('thumbnail_image_url')

    if not all([title, description, category]):
        return jsonify({'msg': '필수 항목 누락'}), 400

    user_id = int(get_jwt_identity())
    
    

    new_post = Post(
        title=title,
        description=description,
        category=category,
        thumbnail_image_url=thumbnail,
        user_id=user_id
    )
    db.session.add(new_post)
    db.session.commit()
    

    return jsonify({'msg': '게시글 등록 완료', 'post_id': new_post.id}), 201

# 게시글 목록 조회 (카테고리 필터, 페이지네이션)
@bp_post.route('', methods=['GET'])
@jwt_required()
def get_post_list():
    category = request.args.get('category')
    try:
        page = max(1, int(request.args.get('page', 1)))
        page = min(page, 1000)  # 과도한 페이지 요청 제한
    except ValueError:
        page = 1
    per_page = min(int(request.args.get('per_page', 10)), 50)

    query = Post.query
    if category:
        query = query.filter_by(category=category)

    pagination = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items

    result = [{
        'id': post.id,
        'title': post.title,
        'description': post.description,
        'category': post.category,
        'thumbnail_image_url': post.thumbnail_image_url,
        'user_id': post.user_id,
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M')
    } for post in posts]

    return jsonify({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'posts': result
    }), 200

# 게시글 상세 조회
@bp_post.route('/<int:postid>', methods=['GET'])
@jwt_required()
def get_post_detail(postid):
    user_id = get_jwt_identity()
    post = Post.query.get(postid)
    if not post:
        return jsonify({'msg': '게시글을 찾을 수 없습니다.'}), 404

    return jsonify({
        'id': post.id,
        'title': post.title,
        'description': post.description,
        'category': post.category,
        'thumbnail_image_url': post.thumbnail_image_url,
        'user_id': post.user_id,
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),

        
    }), 200
#본인 게시물 확인
@bp_post.route('/me', methods=['GET'])
@jwt_required()
def get_my_posts():
    user_id = int(get_jwt_identity())  # 로그인한 사용자 ID
    category = request.args.get('category')
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 10)), 50)

    query = Post.query.filter_by(user_id=user_id)
    
    if category:
        query = query.filter_by(category=category)

    pagination = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items

    result = [{
        'id': post.id,
        'title': post.title,
        'description': post.description,
        'category': post.category,
        'thumbnail_image_url': post.thumbnail_image_url,
        'user_id': post.user_id,
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M')
    } for post in posts]

    return jsonify({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'posts': result
    }), 200


# 게시글 수정
@bp_post.route('/<int:postid>', methods=['PUT'])
@jwt_required()
def update_post(postid):
    user_id = int(get_jwt_identity())
    post = Post.query.get(postid)
    if not post:
        return jsonify({'msg': '게시글을 찾을 수 없습니다.'}), 404
    
    if post.user_id != user_id:
        return jsonify({'msg': '수정 권한이 없습니다.'}), 403

    data = request.get_json()
    post.title = data.get('title', post.title)
    post.description = data.get('description', post.description)
    post.category = data.get('category', post.category)
    post.thumbnail_image_url = data.get('thumbnail_image_url', post.thumbnail_image_url)
    db.session.commit()

    return jsonify({'msg': '게시글 수정 완료'}), 200

# 게시글 삭제
@bp_post.route('/<int:postid>', methods=['DELETE'])
@jwt_required()
def delete_post(postid):
    user_id = int(get_jwt_identity())
    post = Post.query.get(postid)
    if not post:
        return jsonify({'msg': '게시글을 찾을 수 없습니다.'}), 404
    if post.user_id != user_id:
        return jsonify({'msg': '삭제 권한이 없습니다.'}), 403

    db.session.delete(post)
    db.session.commit()

    return jsonify({'msg': '게시글 삭제 완료'}), 200
