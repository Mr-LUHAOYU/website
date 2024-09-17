from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

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

    # 注册
    @staticmethod
    def register(username, password):
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

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

    # 修改密码
    def change_password(self, old_password, new_password):
        if self.password == old_password:
            self.password = new_password
            db.session.commit()
            return True
        return False


class File(db.Model):
    __tablename__ = 'file'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # 多对多关系
    parent_folders = db.relationship('Folder', secondary=file_folder_association, backref='files')

    # 上传
    @staticmethod
    def upload(folder_id, user_id, file_obj):
        file = File(name=file_obj['name'], size=file_obj['size'], owner_id=user_id)
        db.session.add(file)
        db.session.commit()

        # 引用到指定的文件夹
        folder = Folder.query.get(folder_id)
        file.parent_folders.append(folder)
        db.session.commit()
        return file

    # 下载
    @staticmethod
    def download(file_id):
        file = File.query.get(file_id)
        return file

    # 删除
    def delete_if_unreferenced(self):
        if not self.parent_folders:
            db.session.delete(self)
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
    def create(name, owner_id):
        folder = Folder(name=name, owner_id=owner_id)
        db.session.add(folder)
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
