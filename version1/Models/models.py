from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from flask import Flask
# import Models
from Models.config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'


class User(UserMixin, db.Model):
    __tablename__ = 'users_static'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    username2 = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    userkind = db.Column(db.String(50), nullable=False)
    register_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)


class UserDynamic(db.Model):
    __tablename__ = 'users_dynamic'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users_static.id'), nullable=False)
    last_login_time = db.Column(db.DateTime)
    total_submissions = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users_static.id'), nullable=False)
    loc = db.Column(db.String(300), nullable=False)
    fname = db.Column(db.String(300), nullable=False)
    tag = db.Column(db.String(150), nullable=False)
    download_count = db.Column(db.Integer, default=0)


class UploadRecord(db.Model):
    __tablename__ = 'uploads'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users_static.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)


class DownloadRecord(db.Model):
    __tablename__ = 'downloads'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users_static.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    download_time = db.Column(db.DateTime, default=datetime.utcnow)


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    tag_meaning = db.Column(db.String(150), nullable=False)
