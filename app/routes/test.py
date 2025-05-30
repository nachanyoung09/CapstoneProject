from flask import Blueprint, request, jsonify

# 테스트 전용 블루프린트 (기능 확인용)
test_bp = Blueprint('test', __name__, url_prefix='/api/v1')

@test_bp.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'GET':
        return jsonify({"message": "✅ TEST GET 요청 정상 동작"}), 200

    elif request.method == 'POST':
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({'error': 'Missing "text" field'}), 400

        text = data['text']

        # 향후 모델 예측 로직 또는 파이프라인 연결 가능 위치
        return jsonify({
            'prediction': "OK",
            'confidence': 1.0,
            'echo': text
        }), 200
