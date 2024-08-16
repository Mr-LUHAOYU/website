from flask import Flask, session
from flask_session import Session
from config import Config
from models import db

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)

db.init_app(app)
app.config['SESSION_TYPE'] = 'filesystem'  # 使用文件系统存储会话数据
Session(app)
from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
