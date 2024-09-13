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
    __tablename__ = 'user table'
    id = db.Column(db.Integer, primary_key=True)
    # attributes: 用户基本信息 modified=2
    email = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(100))
    birthday = db.Column(db.DateTime)
    sex = db.Column(db.String(10))
    introduction = db.Column(db.String(200))
    avatar = db.Column(db.String(100))

    # attributes: 用户必要信息 modified=1
    username = db.Column(db.String(20))
    password = db.Column(db.String(128))

    # attributes: 用户内置信息 modified=0
    register_time = db.Column(db.DateTime)
    last_login_time = db.Column(db.DateTime)

    # attributes: permission
    read_permission = db.Column(db.Integer, default=1)
    write_permission = db.Column(db.Integer, default=1)
    delete_permission = db.Column(db.Integer, default=1)

    # foreign key
    root_folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))

    def __init__(self, username, password):
        self.username = username
        self.password = generate_password_hash(password)
        self.register_time = datetime.now()
        self.last_login_time = datetime.now()

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def can_write(self, attr, permission=0):
        # permission of self is 1000
        # permission to others is write_others
        return self.write_permission_need(attr) < permission

    def write_permission_need(self, attr):
        if attr in ['email', 'phone', 'address', 'birthday', 'sex', 'introduction', 'avatar']:
            return self.write_permission
        elif attr in ['username']:
            return self.write_permission
        elif attr in ['password']:
            return 999
        else:
            return 9999

    def can_read(self, attr, permission=0):
        # permission of self is 1000
        # permission to others is read_others
        return self.read_permission_need(attr) < permission

    def read_permission_need(self, attr):
        if attr in ['email', 'phone', 'address', 'birthday', 'sex', 'introduction', 'avatar']:
            return self.read_permission
        elif attr in ['username']:
            return self.read_permission
        elif attr in ['password']:
            return 999
        else:
            return 9999

    def can_delete(self, attr, permission=0):
        # permission of self is 1000
        # permission to others is delete_others
        return self.delete_permission < permission


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
