from flask import Flask,send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from sqlalchemy import text
from flask import Flask, send_file
from flask_socketio import SocketIO



socket_io  = SocketIO(cors_allowed_origins= "*")
load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__,static_folder=os.path.join(os.getcwd(), "swagger", "dist"))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    CORS(app)

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
    socket_io.init_app(app)

    @app.route("/ping")
    def ping():
        try:
            db.session.execute(text("SELECT 1"))
            return "✅ RDS 연결 성공", 200
        except Exception as e:
            return f"❌ RDS 연결 실패: {str(e)}", 500

    return app
