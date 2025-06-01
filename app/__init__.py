from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from sqlalchemy import text
from flask_socketio import SocketIO


load_dotenv()

# 확장 객체 정의

socket_io = SocketIO(async_mode='threading', cors_allowed_origins="*")
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

# 앱 생성
def create_app():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SWAGGER_DIR = os.path.join(BASE_DIR, "..", "swagger", "dist")
    OPENAPI_DIR = os.path.join(BASE_DIR, "..")  # openapi.yaml 위치

    app = Flask(__name__, static_folder=SWAGGER_DIR,static_url_path="/docs")

    # 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

    # 확장기능 초기화
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    socket_io.init_app(app)
    CORS(app)

    from app.socket_handlers import register_socketio_handlers #c
    register_socketio_handlers(socket_io) #c

    # 블루프린트 등록
    from app.routes.user import user_bp
    from app.routes.post import bp_post
    from app.routes.trade import bp_trade
    from app.routes.search import search_bp
    from app.routes.valuation import bp_valuation
    from app.routes.test import test_bp
    from app.routes.analytics import bp_analytics
    from app.routes.chat import bp_chat

    app.register_blueprint(user_bp)
    app.register_blueprint(bp_post)
    app.register_blueprint(bp_trade)
    app.register_blueprint(bp_valuation)
    app.register_blueprint(test_bp)
    app.register_blueprint(bp_analytics)
    app.register_blueprint(bp_chat)
    app.register_blueprint(search_bp)

    

    @app.route('/openapi.yaml')
    def openapi_spec():
        return send_from_directory(OPENAPI_DIR, 'openapi.yaml')

    # ✅ DB 연결 확인용 핑
    @app.route("/ping")
    def ping():
        try:
            db.session.execute(text("SELECT 1"))
            return "✅ RDS 연결 성공", 200
        except Exception as e:
            return f"❌ RDS 연결 실패: {str(e)}", 500

    return app
