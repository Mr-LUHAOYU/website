import re
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import shutil
from config import Config
from sqlalchemy import event
from flask import send_file
from sqlalchemy.exc import IntegrityError


db = SQLAlchemy()


file_folder_association = db.Table(
    'file_folder_association',
    db.Column('file_id', db.Integer, db.ForeignKey('file.id'), primary_key=True),
    db.Column('folder_id', db.Integer, db.ForeignKey('folder.id'), primary_key=True)
)

folder_folder_association = db.Table(
    'folder_folder_association',
    db.Column('parent_folder_id', db.Integer, db.ForeignKey('folder.id'),
              primary_key=True),
    db.Column('child_folder_id', db.Integer, db.ForeignKey('folder.id'),
              primary_key=True)
)


# 用户表
class User(db.Model):
    __tablename__ = 'user'
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
    files = db.relationship('File', backref='owner', lazy='dynamic')
    folders = db.relationship('Folder', backref='owner', lazy='dynamic')

    @classmethod
    def register(cls, username, password):
        user = cls(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def login(cls, username, password):
        user = cls.query.filter_by(username=username).first()
        if user and user.check_password(password):
            user.last_login_time = datetime.utcnow()
            db.session.commit()
            return user
        else:
            return None

    @classmethod
    def logout(cls):
        ...

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
    # attributes
    name = db.Column(db.String(100))
    # path = db.Column(db.String(100))
    size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # foreign key
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    parent_folders = db.relationship('Folder', secondary=file_folder_association, backref='files')

    @classmethod
    def create(cls, input_file, author_id, folder_id):
        file = File(
            name=input_file.filename, size=input_file.content_length,
            parent_folder_id=folder_id, owner_id=author_id
        )
        # file.path = f"{file.id}"
        try:
            file.save(input_file)
        except Exception as e:
            print(e)
            return None
        db.session.add(file)
        db.session.commit()
        return file

    def save(self, file):
        with open(str(self.id), 'wb') as f:
            f.write(file.read())

    def delete(self):
        if not self.parent_folders:
            os.remove(str(self.id))
            db.session.delete(self)
            db.session.commit()

    def download(self):
        return send_file(str(self.id), as_attachment=True)

    def get_url(self):
        ...

    def send_to(self, folder_id):
        folder = Folder.query.filter_by(id=folder_id).first()
        if not folder:
            raise ValueError('Folder not found')

        if folder in self.parent_folders:
            print('File already in folder')
            return False

        self.parent_folders.append(folder)
        try:
            db.session.commit()
            print('Folder added successfully')
            return True
        except IntegrityError:
            db.session.rollback()
            print('Folder already exists in folder')
            return False


# 文件夹表
class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # attributes
    name = db.Column(db.String(100))
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    # foreign key
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    parent_folders = db.relationship(
        'Folder',
        secondary=folder_folder_association,
        primaryjoin=(folder_folder_association.c.child_folder_id == id),
        secondaryjoin=(folder_folder_association.c.parent_folder_id == id),
        backref='child_folders'
    )

    @classmethod
    def create(cls, name, author_id, parent_folder_id=0):
        folder = Folder(name=name, parent_folder_id=parent_folder_id, owner_id=author_id)
        db.session.add(folder)
        db.session.commit()
        return folder

    def delete(self):
        for file in self.files:
            ...
        for folder in self.folders:
            folder.delete()
        db.session.delete(self)
        db.session.commit()

    def get_url(self):
        ...


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
