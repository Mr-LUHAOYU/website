import re
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import shutil
from config import Config
from sqlalchemy import event
from flask import send_file

db = SQLAlchemy()


# 用户表
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)


# 用户必要信息
class UserNecessaryInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # attributes
    username = db.Column(db.String(20))
    password = db.Column(db.String(128))
    # foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# 用户基本信息
class UserBasicInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # attributes
    email = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(100))
    birthday = db.Column(db.DateTime)
    sex = db.Column(db.String(10))
    introduction = db.Column(db.String(200))
    avatar = db.Column(db.String(100))
    # foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# 用户内置信息
class UserBuiltinInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # attributes
    register_time = db.Column(db.DateTime)
    last_login_time = db.Column(db.DateTime)
    # foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# 文件表
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)


# 文件夹表
class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)


# 用户权限表
class UserPermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)


# 文件（夹）权限表
class FilePermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)


# 帖子表
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)


# 评论表
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)


# 点赞表
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
