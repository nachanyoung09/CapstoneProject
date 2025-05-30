from app import create_app, socket_io
from flask_migrate import upgrade
from flask import Flask, render_template, send_from_directory, send_file
import requests
import nltk
import matplotlib.pyplot as plt
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from sqlalchemy import text
from flask_cors import CORS
from flask_socketio import SocketIO
from app.socket_handlers import register_socketio_handlers

load_dotenv(dotenv_path=".env")

app = create_app()
socket_io = SocketIO(app, async_mode='threading')
CORS(app)  # Swagger UI 요청 대응 위해 추가

register_socketio_handlers(socket_io)

@app.route('/')
def check_connection():
    try:
        response = requests.get("https://www.google.com", timeout=3)
        return f"Status Code: {response.status_code}, Connected to Google!"
    except requests.exceptions.RequestException as e:
        return f"Connection failed: {e}"

@app.route('/chat/<room_id>')
def chat(room_id):
    return render_template('chat.html', room_id=room_id)

@app.route('/openapi.yaml')
def openapi_spec():
    return send_from_directory('.', 'openapi.yaml')

# ✅ Swagger UI 라우팅 추가
@app.route('/docs')
def swagger_ui():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/docs/<path:path>')
def send_swagger_files(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    with app.test_client() as client:
        upgrade()
        print('\n\U0001F4E6 테스트 요청 시작...\n')

        response = client.post('/api/v1/users/login', json={"username": "user1", "password": "pw1"})
        print('✅ 응답 결과:', response.get_json(), '\n')

        response = client.get('/api/v1/search')
        print('✅ 응답 결과:', response.get_json(), '\n')

        response = client.post('/api/v1/users/register', json={"username": "user1"})
        print('✅ 응답 결과:', response.get_json(), '\n')

    socket_io.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
