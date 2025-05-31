import os
import re
import pickle
import numpy as np
from flask import Blueprint, request, jsonify
from app import db
from app.models.post import Post
from datetime import datetime
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz

# 하이브리드 검색 설정
MODEL_NAME = "all-MiniLM-L6-v2"
EMB_CACHE = "emb_titles.pkl"  # 임시 캐시 파일 경로
TOP_N = 20
ALPHA = 0.5  # SBERT 50% / BM25 50%
FUZZY_THRESH = 60  # fuzzy 매칭 임계값

# 동의어 정규화 사전
SYNONYMS = {
    # 브랜드
    "나이키":    ["나이키", "nike"],
    "니케":      ["니케"],
    "아디다스":  ["아디다스", "adidas"],
    "뉴발란스":  ["뉴발란스", "new balance", "newbalance", "nb"],
    "컨버스":    ["컨버스", "converse"],
    "푸마":      ["푸마", "puma"],
    "언더아머":  ["언더아머", "under armour", "underarmor", "ua"],
    "반스":      ["반스", "vans"],
    "리복":      ["리복", "reebok"],
    "아식스":    ["아식스", "asics"],

    # 신발류
    "신발":      ["신발", "운동화"],
    "스니커즈":  ["스니커즈", "sneakers"],
    "러닝화":    ["러닝화", "running shoes", "running"],
    "구두":      ["구두"],
    "부츠":      ["부츠", "boots"],
    "샌들":      ["샌들", "sandals"],
    "플립플랍":  ["플립플랍", "flip flop"],

    # 의류
    "티셔츠":    ["티셔츠", "t-shirt", "tee"],
    "반팔티":    ["반팔티", "short sleeve tee"],
    "긴팔티":    ["긴팔티", "long sleeve tee"],
    "맨투맨":    ["맨투맨", "sweatshirt", "sweater"],
    "후디":      ["후디", "hoodie", "hooded sweatshirt"],
    "셔츠":      ["셔츠", "shirt", "blouse"],
    "자켓":      ["자켓", "jacket", "bomber"],
    "코트":      ["코트", "coat", "overcoat"],
    "패딩":      ["패딩", "puffer jacket"],
    "청바지":    ["청바지", "jeans", "denim"],
    "조거팬츠":  ["츄리닝", "조거팬츠", "jogger", "track pants"],
    "원피스":    ["원피스", "dress"],

    # 가방/지갑
    "백팩":      ["백팩", "backpack"],
    "토트백":    ["토트백", "tote bag"],
    "크로스백":  ["크로스백", "cross bag", "crossbody"],
    "클러치":    ["클러치", "clutch"],
    "지갑":      ["지갑", "wallet"],

    # 액세서리
    "모자":      ["모자", "cap", "hat", "beanie"],
    "시계":      ["시계", "watch"],
    "선글라스":  ["선글라스", "sunglasses"],
    "안경":      ["안경", "glasses"],
    "팔찌":      ["팔찌", "bracelet"],
    "목걸이":    ["목걸이", "necklace"],
    "반지":      ["반지", "ring"],

    # 전자기기
    "핸드폰":    ["핸드폰", "휴대폰", "mobile", "cellphone"],
    "아이폰":    ["아이폰", "iphone"],
    "갤럭시":    ["갤럭시", "galaxy"],
    "태블릿":    ["태블릿", "tablet", "ipad"],
    "노트북":    ["노트북", "laptop", "macbook"],
    "카메라":    ["카메라", "camera", "dslr"],
    "이어폰":    ["이어폰", "earphones", "earbuds"],

    # 스포츠/취미
    "티켓":      ["티켓", "ticket"],
    "콘서트":    ["콘서트", "concert"],
    "자전거":    ["자전거", "bike"],
    "캠핑용품":  ["텐트", "캠핑의자", "캠핑테이블", "camping"],
    "낚시용품":  ["낚시대", "릴", "낚시용품"],

    # 굿즈/피규어
    "포켓몬씰":  ["포켓몬씰", "띠부씰"],
    "포카":      ["포카", "포토카드", "photo card"],
    "피규어":    ["피규어", "figure"],

    # 거래상태/행위
    "새상품":    ["새상품", "새제품", "미개봉", "unopened"],
    "중고":      ["중고", "used"],
    "교환":      ["교환", "swap", "교환원함"],
    "판매":      ["판매", "팝니다", "for sale"],
    "구매":      ["구매", "삽니다", "want to buy"],

    # 기타
    "사이즈":    ["사이즈", "size"],
    "택포":      ["택포", "배송비포함"],
    "정품":      ["정품", "authentic"],
    "리퍼":      ["리퍼", "refurbished"],
    "박스풀":    ["박스풀", "full box"],
    "추가금":    ["추가금", "extra charge"],
}

search_bp = Blueprint("search", __name__, url_prefix="/api/v1/search")


def normalize(text: str) -> str:
    txt = text.lower()
    for canon, variants in SYNONYMS.items():
        pattern = r"\b(" + "|".join(map(re.escape, variants)) + r")\b"
        txt = re.sub(pattern, canon, txt)
    return re.sub(r"\s+", " ", txt).strip()


def preprocess(text: str) -> str:
    txt = text.lower()
    txt = re.sub(r"[^\w\s가-힣]", " ", txt)
    return normalize(txt)


def load_or_build_embeddings(pre_titles, model_name, cache_path):
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            emb = pickle.load(f)
        print(f"> SBERT 임베딩 캐시 로드: {cache_path}")
    else:
        print("> SBERT 임베딩 생성 중...")
        model = SentenceTransformer(model_name)
        emb = model.encode(pre_titles, normalize_embeddings=True, show_progress_bar=True)
        with open(cache_path, "wb") as f:
            pickle.dump(emb, f)
        print(f"> SBERT 임베딩 저장: {cache_path}")
    return emb


def build_bm25(tokenized_titles):
    return BM25Okapi(tokenized_titles)


def hybrid_rank(raw_titles, pre_titles, emb_titles, bm25, query, alpha, top_n):
    q = preprocess(query)
    tokens = q.split()

    # 후보 필터링 (싱글 매칭 + 전체 쿼리 token_set_ratio)
    mask = []
    for title in pre_titles:
        toks = title.split()
        keep = any(
            (tok in toks) or
            any(fuzz.partial_ratio(tok, w) >= FUZZY_THRESH for w in toks)
            for tok in tokens
        )
        if not keep and fuzz.token_set_ratio(q, title) >= FUZZY_THRESH:
            keep = True
        mask.append(keep)
    mask = np.array(mask, dtype=bool)

    # SBERT 유사도
    sbert = SentenceTransformer(MODEL_NAME)
    q_emb = sbert.encode([q], normalize_embeddings=True)[0]
    sbert_sims = cosine_similarity([q_emb], emb_titles)[0]

    # BM25 유사도
    bm25_scores = np.array(bm25.get_scores(tokens), dtype=float)
    if bm25_scores.max() > 0:
        bm25_scores /= bm25_scores.max()

    # 하이브리드 스코어
    hybrid_scores = alpha * sbert_sims + (1 - alpha) * bm25_scores

    # 필터링된 인덱스
    idxs = np.where(mask)[0]

    # 부스트 적용
    boosted = []
    for idx in idxs:
        score = hybrid_scores[idx]
        raw = raw_titles[idx].lower()
        if q in raw:
            score += 0.5
        elif fuzz.partial_ratio(q, raw) >= FUZZY_THRESH:
            score += 0.2
        boosted.append((idx, score))

    # 정렬 및 Top-N 선택
    boosted.sort(key=lambda x: x[1], reverse=True)
    results = boosted[:top_n]

    # 부족 시 BM25 보충
    if len(results) < top_n:
        needed = top_n - len(results)
        order = np.argsort(bm25_scores)[::-1]
        for idx in order:
            if idx not in idxs:
                results.append((idx, hybrid_scores[idx]))
                if len(results) >= top_n:
                    break

    return [(raw_titles[i], float(s)) for i, s in results[:top_n]]


# 기존 검색 엔드포인트 (title과 category를 AND 조건으로 검색)
@search_bp.route('', methods=['GET'])
def search_posts():
    title = request.args.get('title', type=str)
    category = request.args.get('category', type=str)

    if not title and not category:
        return jsonify({"status": "error", "message": "title 또는 category 파라미터가 필요합니다."}), 400

    query = Post.query
    if title:
        query = query.filter(Post.title.ilike(f'%{title}%'))
    if category:
        query = query.filter(Post.category.ilike(f'%{category}%'))

    posts = query.order_by(Post.created_at.desc()).all()

    result = [{
        "id": p.id,
        "title": p.title,
        "user_id": p.user_id,
        "category": p.category,
        "created_at": p.created_at.strftime('%Y-%m-%d') if p.created_at else None
    } for p in posts]

    return jsonify({
        "status": "success",
        "count": len(result),
        "posts": result
    }), 200


# 심화 검색 엔드포인트 (title만 대상으로 하이브리드 검색)
@search_bp.route('/advanced', methods=['GET'])
def advanced_search():
    title = request.args.get('title', type=str)

    if not title:
        return jsonify({"status": "error", "message": "title 파라미터가 필요합니다."}), 400

    # 최신 5000개 게시글 조회
    posts = Post.query.order_by(Post.created_at.desc()).limit(5000).all()

    if not posts:
        return jsonify({
            "status": "success",
            "count": 0,
            "posts": []
        }), 200

    # 제목과 ID 수집
    raw_titles = [post.title for post in posts]
    post_ids = [post.id for post in posts]
    pre_titles = [preprocess(title) for title in raw_titles]

    # 임베딩 로드 또는 생성
    emb_titles = load_or_build_embeddings(pre_titles, MODEL_NAME, EMB_CACHE)

    # BM25 모델 생성
    bm25 = build_bm25([t.split() for t in pre_titles])

    # 하이브리드 검색 수행
    results = hybrid_rank(raw_titles, pre_titles, emb_titles, bm25, title, ALPHA, TOP_N)

    # 결과 포맷팅
    result = []
    for title_text, _ in results:
        for post in posts:
            if post.title == title_text:
                result.append({
                    "id": post.id,
                    "title": post.title,
                    "user_id": post.user_id,
                    "category": post.category,
                    "created_at": post.created_at.strftime('%Y-%m-%d') if post.created_at else None
                })
                break

    return jsonify({
        "status": "success",
        "count": len(result),
        "posts": result
    }), 200