from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import shutil
from config import Config

db = SQLAlchemy()


class UserStaticInfo(db.Model):
    __tablename__ = 'user_static'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registered_on = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    is_logged_in = db.Column(db.Boolean, default=False)
    permission_level = db.Column(db.Integer, default=1)

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class UserDynamicInfo(db.Model):
    __tablename__ = 'user_dynamic'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    real_name = db.Column(db.String(100))
    student_id = db.Column(db.String(10))
    root_folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'))

    # files = db.relationship('File', backref='author', lazy=True)
    # folders = db.relationship('Folder', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def delete(self):
        root = Folder.query.filter_by(id=self.root_folder_id).first()
        root.delete()
        db.session.delete(self)
        db.session.commit()


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, default=100000)
    static_info = db.relationship('UserStaticInfo', uselist=False, backref='user')
    dynamic_info = db.relationship('UserDynamicInfo', uselist=False, backref='user')

    @classmethod
    def createUser(cls, username, password, ):
        user = User()
        user.dynamic_info = UserDynamicInfo(username=username)
        user.dynamic_info.set_password(password)
        user.static_info = UserStaticInfo()
        path = Config.IMG_PATH(user.uid)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        path = Config.BIO_PATH(user.uid)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        path = Config.ROOT_PATH(user.uid)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        user.dynamic_info.root_folder_id = Folder.create('root', None, user).id
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def getUserByUsername(cls, username):
        return User.query.join(UserDynamicInfo).filter(UserDynamicInfo.username == username).first()

    def delete(self):
        self.dynamic_info.delete()
        self.static_info.delete()
        path = Config.IMG_PATH(self.uid)
        os.remove(path)
        path = Config.BIO_PATH(self.uid)
        os.remove(path)
        path = Config.ROOT_PATH(self.uid)
        shutil.rmtree(path)
        db.session.delete(self)
        db.session.commit()


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    filename = db.Column(db.String(150), nullable=False)
    uploaded_on = db.Column(db.DateTime, default=datetime.utcnow)
    download_count = db.Column(db.Integer, default=0)
    tags = db.Column(db.String(200))

    @property
    def author_name(self):
        author = User.query.filter_by(id=self.author_id).first()
        return author.dynamic_info.username

    @property
    def author_uid(self):
        author = User.query.filter_by(id=self.author_id).first()
        return author.uid

    @property
    def PATH(self) -> str:
        # the absolute path of the file is root/PATH
        return self.folder.PATH + '/' + self.filename

    def delete(self, path):
        os.remove(os.path.join(Config.UPLOAD_FOLDER(self.author_uid), path))
        db.session.delete(self)
        db.session.commit()

    def rename(self, new_filename):
        os.rename(os.path.join(Config.UPLOAD_FOLDER(self.author_uid), self.filename),
                  os.path.join(Config.UPLOAD_FOLDER(self.author_uid), new_filename))
        self.filename = new_filename
        db.session.commit()

    def move(self, new_folder):
        os.rename(os.path.join(Config.UPLOAD_FOLDER(self.author_uid), self.PATH),
                  os.path.join(Config.UPLOAD_FOLDER(self.author_uid), new_folder.PATH + '/' + self.filename))
        self.folder = new_folder
        db.session.commit()

    @classmethod
    def create(cls, input_file, folder, author, tags=None):
        file = cls(filename=input_file.filename, folder=folder, author=author)
        author.dynamic_info.files.append(file)
        if tags is not None:
            file.tags = tags
        input_file.save(os.path.join(Config.UPLOAD_FOLDER(author.uid), file.PATH))
        db.session.add(file)
        db.session.commit()
        return file


class Folder(db.Model):
    __tablename__ = 'folders'
    id = db.Column(db.Integer, primary_key=True)
    folder_name = db.Column(db.String(150), nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    # parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    children = db.relationship(
        'Folder', backref=db.backref('parent', remote_side=[id]),
        cascade='all, delete-orphan'
    )
    files = db.relationship(
        'File', backref='folder', lazy=True,
        cascade='all, delete-orphan'
    )

    @property
    def author_name(self):
        return self.author.dynamic_info.username

    @property
    def author_uid(self):
        return self.author.uid

    @property
    def PATH(self) -> str:
        # the absolute path of the folder is root/PATH
        path = []
        current_folder = self
        while current_folder is not None:
            path.append(current_folder.folder_name)
            current_folder = current_folder.parent
        return '/'.join(reversed(path))

    def remove(self, path):
        os.remove(os.path.join(Config.UPLOAD_FOLDER(self.author_uid), path))

    def delete(self):
        for child in self.children:
            child.delete()
        for file in self.files:
            file.delete()
        db.session.delete(self)
        db.session.commit()

    def rename(self, new_folder_name):
        os.rename(os.path.join(Config.UPLOAD_FOLDER(self.author_uid), self.PATH),
                  os.path.join(Config.UPLOAD_FOLDER(self.author_uid), new_folder_name))
        self.folder_name = new_folder_name
        db.session.commit()

    def move(self, new_folder):
        shutil.move(
            Config.UPLOAD_FOLDER(self.author_uid) + self.PATH,
            Config.UPLOAD_FOLDER(self.author_uid) + new_folder.PATH + '/' + self.folder_name
        )
        self.parent.children.remove(self)
        new_folder.children.append(self)
        self.parent = new_folder
        db.session.commit()

    @classmethod
    def create(cls, folder_name, parent, author):
        folder = cls(folder_name=folder_name, parent=parent, author=author)
        author.dynamic_info.folders.append(folder)
        db.session.add(folder)
        db.session.commit()
        return folder
