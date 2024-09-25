from datetime import datetime
from flask import flash
from flask_sqlalchemy import SQLAlchemy
from config import Config
import re
from IO2OSS import *

db = SQLAlchemy()

# 文件和文件夹之间的多对多关联表
file_folder_association = db.Table(
    'file_folder_association',
    db.Column('file_id', db.Integer, db.ForeignKey('file.id'), primary_key=True),
    db.Column('folder_id', db.Integer, db.ForeignKey('folder.id'), primary_key=True)
)

# 文件夹和文件夹之间的自关联表（父文件夹和子文件夹）
folder_folder_association = db.Table(
    'folder_folder_association',
    db.Column('parent_folder_id', db.Integer, db.ForeignKey('folder.id'), primary_key=True),
    db.Column('child_folder_id', db.Integer, db.ForeignKey('folder.id'), primary_key=True)
)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    # 关系
    files = db.relationship('File', backref='owner', lazy='dynamic')
    folders = db.relationship('Folder', backref='owner', lazy='dynamic')
    posts = db.relationship('Post', backref='owner', lazy='dynamic')
    comments = db.relationship('Comment', backref='owner', lazy='dynamic')

    # attributes: 用户基本信息 modified=2
    email = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(100))
    birthday = db.Column(db.DateTime)
    sex = db.Column(db.String(10))
    real_name = db.Column(db.String(20))
    student_id = db.Column(db.String(20))
    introduction = db.Column(db.String(200))
    avatar = db.Column(db.String(100))

    # attributes: 用户内置信息 modified=0
    register_time = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_time = db.Column(db.DateTime, default=datetime.utcnow)

    # 注册
    @staticmethod
    def register(username, password):
        user = User(username=username, password=password)

        db.session.add(user)
        db.session.commit()

        user.avatar = Config.IMG_PATH(user.id)
        db.session.commit()

        # 为新用户创建一个存放头像和个人简介的文件夹
        path = 'static/' + Config.IMG_PATH(user.id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write('')
        path = 'static/' + Config.BIO_PATH(user.id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write('')

        # 为新用户创建一个名为 root 的文件夹
        root_folder = Folder(name='root', owner_id=user.id)
        db.session.add(root_folder)
        db.session.commit()
        return user

    # 登录
    @staticmethod
    def login(username, password):
        user = User.query.filter_by(username=username, password=password).first()
        return user

    def logout(self):
        pass

    # 修改密码
    def set_password(self, password):
        self.password = password
        db.session.commit()

    def change_img(self, img):
        img.save(f'static/{self.avatar}')
        return True

    def delete(self):
        ...

    def update_info(self, username=None, password=None, email=None,
                    phone=None, real_name=None, student_id=None):
        if password:
            return self.set_password(password)
        for it in ['username', 'email', 'phone', 'real_name', 'student_id']:
            if eval(it):
                phone_regex = r'^1[3-9]\d{9}$'
                if it == 'phone' and re.match(phone_regex, phone) is None:
                    flash('手机号码格式错误')
                if it == 'phone':
                    if User.query.filter_by(phone=eval(it)).first():
                        flash('手机号码已存在')
                if it == 'username':
                    if User.query.filter_by(username=eval(it)).first() and self.username != eval(it):
                        flash('用户名已存在')
                if it == 'email':
                    if User.query.filter_by(email=eval(it)).first():
                        flash('邮箱已存在')
                if it == 'student_id':
                    if User.query.filter_by(student_id=eval(it)).first():
                        flash('学号已存在')
                exec(f"self.{it} = {it}")
        db.session.commit()


class File(db.Model):
    __tablename__ = 'file'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_on = db.Column(db.DateTime, default=datetime.utcnow)
    # 多对多关系
    parent_folders = db.relationship('Folder', secondary=file_folder_association, backref='files')

    # 上传
    @staticmethod
    def upload(folder_id, user_id, file_obj):
        file = File(name=file_obj.filename, size=file_obj.content_length, owner_id=user_id)
        db.session.add(file)
        db.session.commit()

        # 引用到指定的文件夹
        folder = Folder.query.get(folder_id)
        file.parent_folders.append(folder)
        db.session.commit()

        # 保存文件
        # path = Config.FILE_PATH(file.id)
        # os.makedirs(os.path.dirname(path), exist_ok=True)
        file_obj.save(str(file.id))
        upload_to_oss(str(file.id), str(file.id))
        return file

    # 下载
    @staticmethod
    def download(file_id):
        file = File.query.get(file_id)
        filestream = download_from_oss(str(file.id))
        return filestream, file.name

    # 删除文件
    def delete_if_unreferenced(self):
        if not self.parent_folders:
            # path = Config.FILE_PATH(self.id)
            # os.remove(path)
            delete_from_oss(str(self.id))
            db.session.delete(self)
            db.session.commit()

    def delete(self):
        for folder in self.parent_folders:
            folder.files.remove(self)    # 从文件夹中移除引用
        self.delete_if_unreferenced()    # 删除文件
        db.session.commit()

    # 共享
    def share_to(self, folder_id):
        folder = Folder.query.get(folder_id)
        if folder and folder not in self.parent_folders:
            self.parent_folders.append(folder)
            db.session.commit()


class Folder(db.Model):
    __tablename__ = 'folder'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # 自关联多对多关系
    parent_folders = db.relationship(
        'Folder', secondary=folder_folder_association,
        primaryjoin=(folder_folder_association.c.child_folder_id == id),
        secondaryjoin=(folder_folder_association.c.parent_folder_id == id),
        backref='child_folders'
    )

    # 创建
    @staticmethod
    def create(name, owner_id, parent_id):
        folder = Folder(name=name, owner_id=owner_id)
        db.session.add(folder)
        db.session.commit()
        parent_folder = Folder.query.filter_by(id=parent_id).first()
        # print(parent_id)
        folder.parent_folders.append(parent_folder)
        db.session.commit()
        return folder

    # 删除
    def delete_if_unreferenced(self):
        if not self.parent_folders:
            for file in self.files:
                file.delete_if_unreferenced()
            for child_folder in self.child_folders:
                child_folder.delete_if_unreferenced()
            db.session.delete(self)
            db.session.commit()

    def delete(self, parent_folder_id):
        self.parent_folders.remove(Folder.query.get(parent_folder_id))
        self.delete_if_unreferenced()
        db.session.commit()

    # 共享
    def share_to(self, folder_id):
        parent_folder = Folder.query.get(folder_id)
        if parent_folder and parent_folder not in self.parent_folders:
            self.parent_folders.append(parent_folder)
            db.session.commit()


class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # 创建
    @staticmethod
    def create(title, content, owner_id):
        post = Post(title=title, content=content, owner_id=owner_id)
        db.session.add(post)
        db.session.commit()
        return post

    # 编辑
    def edit(self, title, content):
        self.title = title
        self.content = content
        db.session.commit()

    # 删除
    def delete(self):
        for comment in self.comments:
            db.session.delete(comment)
        db.session.delete(self)
        db.session.commit()

    # 点赞
    def like(self, user_id):
        self.likes += 1
        db.session.commit()

    # 评论
    def comment(self, user_id, content):
        comment = Comment(content=content, owner_id=user_id, post_id=self.id)
        db.session.add(comment)
        db.session.commit()
        return comment


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    # 创建
    @staticmethod
    def create(content, owner_id, post_id):
        comment = Comment(content=content, owner_id=owner_id, post_id=post_id)
        db.session.add(comment)
        db.session.commit()
        return comment

    # 编辑
    def edit(self, content):
        self.content = content
        db.session.commit()

    # 删除
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    # 点赞
    def like(self, user_id):
        self.likes += 1
        db.session.commit()
