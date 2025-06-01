import os
from app import create_app, socket_io,db
from flask_migrate import init, migrate, stamp, upgrade
from sqlalchemy import text


app = create_app()


# ✅ 마이그레이션 및 테스트는 앱 컨텍스트 내에서만 가능
if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists('migrations'):
            init()
            stamp()
        migrate(message="Auto migration")
        # 마이그레이션 실행
        upgrade()

        # 테스트 요청 실행
        with app.test_client() as client:
            print('\n📦 테스트 요청 시작...\n')

            response = client.post('/api/v1/users/login', json={"username": "user1", "password": "pw1"})
            print('✅ 로그인 응답:', response.get_json(), '\n')

            response = client.get('/api/v1/search')
            print('✅ 검색 응답:', response.get_json(), '\n')

            response = client.post('/api/v1/users/register', json={"username": "user1"})
            print('✅ 회원가입 응답:', response.get_json(), '\n')

    # ✅ Flask SocketIO 실행
    socket_io.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )
