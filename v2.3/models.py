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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    registered_on = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    is_logged_in = db.Column(db.Boolean, default=False)
    permission_level = db.Column(db.Integer, default=1)
    upload_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def uid(self):
        return self.user.uid


class UserDynamicInfo(db.Model):
    __tablename__ = 'user_dynamic'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    real_name = db.Column(db.String(100))
    student_id = db.Column(db.String(10))
    root_folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def delete(self):
        root = Folder.query.filter_by(id=self.root_folder_id).first()
        root.delete()
        db.session.delete(self)
        db.session.commit()

    def change_img(self, img):
        path = Config.IMG_PATH(self.user.uid)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        img.save(path)

    def uid(self):
        return self.user.uid


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, default=100000)
    static_info = db.relationship('UserStaticInfo', uselist=False, backref='user')
    dynamic_info = db.relationship('UserDynamicInfo', uselist=False, backref='user')

    @staticmethod
    def check_username_exist(username):
        return UserDynamicInfo.query.filter_by(username=username).first() is not None

    @classmethod
    def register(cls, username, password, ):
        user = cls()
        db.session.add(user)
        db.session.commit()
        udi = UserDynamicInfo(username=username)
        usi = UserStaticInfo()
        udi.user_id = user.id
        usi.user_id = user.id
        udi.set_password(password)
        db.session.add(udi)
        db.session.add(usi)
        db.session.commit()
        path = Config.IMG_PATH(user.uid)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write('')
        path = Config.BIO_PATH(user.uid)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write('')
        # path = Config.ROOT_PATH(user.uid)
        # os.makedirs(os.path.dirname(path+'/no'), exist_ok=True)
        user.dynamic_info.root_folder_id = Folder.create('root', None, user.id).id
        # db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def getUserByUsername(cls, username):
        return User.query.join(UserDynamicInfo).filter(UserDynamicInfo.username == username).first()

    def delete(self):
        self.dynamic_info.delete()
        self.static_info.delete()
        os.rmdir(os.path.dirname(Config.IMG_PATH(self.uid)))
        os.rmdir(os.path.dirname(Config.UPLOAD_FOLDER(self.uid)))
        db.session.delete(self)
        db.session.commit()

    def update_info(self, username=None, password=None, email=None,
                    phone=None, real_name=None, student_id=None):
        if password is not None:
            self.dynamic_info.set_password(password)
        for it in ['username', 'email', 'phone', 'real_name', 'student_id']:
            if eval(it) is not None:
                exec(f"self.dynamic_info.{it} = {it}")
        db.session.commit()

    def login(self):
        self.static_info.is_logged_in = True
        self.static_info.last_login = datetime.utcnow()
        db.session.commit()

    def logout(self):
        self.static_info.is_logged_in = False
        db.session.commit()

    def upload(self, file, folder="root", tags=None):
        if folder == "root":
            folder = Folder.query.filter_by(id=self.dynamic_info.root_folder_id).first()
        if File.create(file, folder, self, tags):
            self.static_info.upload_count += 1
            db.session.commit()
            return True
        else:
            return False

    def download(self, file):
        ...

    def change_img(self, img):
        self.dynamic_info.change_img(img)


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'))
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
        return self.folder.PATH + '/' + self.filename

    def delete(self, first=True):
        if first:
            os.remove(self.PATH)
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
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'))
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
    def PATH(self) -> str:
        path = []
        current_folder = self
        while current_folder is not None:
            path.append(current_folder.folder_name)
            current_folder = current_folder.parent
        path = '/'.join(reversed(path))
        author = User.query.filter_by(id=self.author_id).first()
        path = os.path.join(Config.UPLOAD_FOLDER(author.uid), path)
        return path

    def delete(self, first=True):
        for child in self.children:
            child.delete(False)
        for file in self.files:
            file.delete(False)
        if first:
            shutil.rmtree(self.PATH)
        db.session.delete(self)
        db.session.commit()

    def rename(self, new_folder_name):
        os.rename(self.PATH, new_folder_name)
        self.folder_name = new_folder_name
        db.session.commit()

    def move(self, new_folder):
        shutil.move(
            self.PATH,
            new_folder.PATH + '/' + self.folder_name
        )
        self.parent.children.remove(self)
        new_folder.children.append(self)
        self.parent = new_folder
        db.session.commit()

    @classmethod
    def create(cls, folder_name, parent_id, author_id):
        folder = cls(folder_name=folder_name, parent=parent_id, author_id=author_id)
        db.session.add(folder)
        db.session.commit()
        os.makedirs(folder.PATH, exist_ok=True)
        return folder
