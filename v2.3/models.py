import re
import smtplib
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import shutil
from config import Config
from sqlalchemy import event
from flask import send_file

# from flask.request import FileStorage

db = SQLAlchemy()

# 中间表用于 File 和 Folder 的多对多关系
file_folder_association = db.Table(
    'file_folder_association',
    db.Column('file_id', db.Integer, db.ForeignKey('file.id'), primary_key=True),
    db.Column('folder_id', db.Integer, db.ForeignKey('folder.id'), primary_key=True)
)

# 中间表用于 Folder 的自引用多对多关系
folder_folder_association = db.Table(
    'folder_folder_association',
    db.Column('parent_folder_id', db.Integer, db.ForeignKey('folder.id'),
              primary_key=True),
    db.Column('child_folder_id', db.Integer, db.ForeignKey('folder.id'),
              primary_key=True)
)


class UserStaticInfo(db.Model):
    __tablename__ = 'user_static'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    registered_on = db.Column(db.DateTime, default=lambda: datetime.utcnow() + Config.TIME_DELTA)
    last_login = db.Column(db.DateTime, default=lambda: datetime.utcnow() + Config.TIME_DELTA)
    is_logged_in = db.Column(db.Boolean, default=False)
    permission_level = db.Column(db.Integer, default=1)
    upload_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)

    def login(self):
        self.is_logged_in = True
        self.last_login = datetime.utcnow() + Config.TIME_DELTA
        db.session.commit()

    def logout(self):
        self.is_logged_in = False
        db.session.commit()

    def levelUp(self):
        self.permission_level += 1
        db.session.commit()

    def levelDown(self):
        self.permission_level -= 1
        db.session.commit()

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
    root_folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        valid, msg = self.password_valid(password)
        if valid:
            self.password_hash = generate_password_hash(password)
            db.session.commit()
        return msg

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def password_valid(password) -> [bool, str]:
        if not 6 <= len(password) <= 18:
            return False, "密码长度必须大于等于6位小于等于18位"
        if not any(char.isdigit() for char in password):
            return False, "密码必须同时包含字母和数字"
        if not any(char.isalpha() for char in password):
            return False, "密码必须同时包含字母和数字"
        return True, "密码修改成功"

    @staticmethod
    def email_valid(email):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if re.match(email_regex, email) is None:
            return False
        return True
        # 检查域名是否存在
        # domain = email.split('@')[1]
        # try:
        #     server = smtplib.SMTP()
        #     server.set_debuglevel(0)
        #     server.connect(domain, 10)
        #     server.helo(domain)
        #     server.quit()
        #     return True
        # except:
        #     return False

    @staticmethod
    def phone_valid(phone):
        phone_regex = r'^1[3-9]\d{9}$'
        if re.match(phone_regex, phone) is None:
            return False
        return True

    @staticmethod
    def student_id_valid(student_id):
        return True

    @staticmethod
    def real_name_valid(real_name):
        return True

    @staticmethod
    def username_valid(username):
        return True

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
        # user.uid = user.id
        # User.uid += 1
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
        shutil.rmtree(os.path.dirname(Config.IMG_PATH(self.uid)))
        shutil.rmtree(os.path.dirname(Config.UPLOAD_FOLDER(self.uid)))
        db.session.delete(self)
        db.session.commit()

    def update_info(self, username=None, password=None, email=None,
                    phone=None, real_name=None, student_id=None):
        if password:
            return self.dynamic_info.set_password(password)
        for it in ['username', 'email', 'phone', 'real_name', 'student_id']:
            # print(f"self.dynamic_info.{it}_valid({it})")
            if eval(it) and eval(f"self.dynamic_info.{it}_valid({it})"):
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
        if type(folder) is Folder:
            folder = folder.id
        if File.create(file, folder, self.id, tags):
            self.static_info.upload_count += 1
            db.session.commit()
            return True
        else:
            return False

    def download(self, file):
        ...

    def change_img(self, img):
        self.dynamic_info.change_img(img)

#     @property
#     def to_html(self):
#         root_folder = Folder.query.filter_by(id=self.dynamic_info.root_folder_id).first()
#         html, cnt = root_folder.to_html()
#         script = ""
#         for i in range(cnt + 1):
#             script += f"""
# <script>
# document.getElementById('folderForm{i}').addEventListener('submit', function(event) {{
#     const form = event.target;
#     const action = form.action.value;
#
#     if (action === 'upload') {{
#
#         form.submit(); // 提交表单
#         }}else if (action === 'new_folder') {{
#         const newName = prompt('请输入新的文件夹名称:');
#         if (newName) {{
#         form.folder_name.value = newName;
#         form.submit(); // 提交表单
#         }} }}
# }});
# </script>
# """
#         return html, script

    def html_code(self):
        root_folder = Folder.query.filter_by(id=self.dynamic_info.root_folder_id).first()
        return root_folder.html_code()


class File(db.Model):
    __tablename__ = 'file'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'))
    filename = db.Column(db.String(150), nullable=False)
    uploaded_on = db.Column(db.DateTime, default=datetime.utcnow)
    download_count = db.Column(db.Integer, default=0)
    tags = db.Column(db.String(200))
    cite_times = db.Column(db.Integer, default=1)
    folders = db.relationship('Folder', secondary=file_folder_association, backref='files')

    # @property
    # def author_name(self):
    #     author = User.query.filter_by(id=self.author_id).first()
    #     return author.dynamic_info.username

    # @property
    # def author_uid(self):
    #     author = User.query.filter_by(id=self.author_id).first()
    #     return author.uid

    # @property
    # def PATH(self):
    #     parent_folder = Folder.query.filter_by(id=self.folder_id).first()
    #     return parent_folder.PATH + '/' + self.filename
    #     return f"{Config.UPLOAD_FOLDER(self.author_uid)}/{self.id}"

    @property
    def PATH(self):
        # return rf"F:\website\workspace\v2.3\files\{self.id}"
        # return rf"\v2.3\files\{self.id}"
        return rf"files\{self.id}"
        # return rf"E:\Web Project\WEB\v2.3\files\{self.id}"


    # def delete(self, first=True):
    #     if first:
    #         os.remove(self.PATH)
    #     db.session.delete(self)
    #     db.session.commit()
    def delete(self):
        self.decrease_cite_times()

    def decrease_cite_times(self):
        self.cite_times -= 1
        if self.cite_times == 0:
            os.remove(self.PATH)
            db.session.delete(self)
        db.session.commit()

    def increase_cite_times(self):
        self.cite_times += 1
        db.session.commit()

    def rename(self, new_filename):
        # os.rename(os.path.join(Config.UPLOAD_FOLDER(self.author_uid), self.filename),
        #           os.path.join(Config.UPLOAD_FOLDER(self.author_uid), new_filename))
        self.filename = new_filename
        db.session.commit()

    # def move(self, new_folder):
    #     os.rename(os.path.join(Config.UPLOAD_FOLDER(self.author_uid), self.PATH),
    #               os.path.join(Config.UPLOAD_FOLDER(self.author_uid), new_folder.PATH + '/' + self.filename))
    #     self.folder_id = new_folder.id
    #     db.session.commit()

    def copy(self, folder=None, folder_id=None):
        if folder is None and folder_id is None:
            return
        if folder_id is not None:
            folder = Folder.query.filter_by(id=folder_id).first()
        folder.files.append(self)
        self.folders.append(folder)
        self.cite_times += 1
        db.session.commit()

    def download(self):
        self.download_count += 1
        db.session.commit()
        return send_file(self.PATH, as_attachment=True)

    @classmethod
    def create(cls, input_file, folder_id, author_id, tags=None):
        folder = Folder.query.filter_by(id=folder_id).first()
        filename = input_file.filename
        name, ext = os.path.splitext(filename)  # 分离文件名和扩展名
        if folder.check_has_file(filename):
            filename = f"{name}(1){ext}"
        restr = r"(.*)\((\d+)\)(\.\w+)$"
        while folder.check_has_file(filename):
            match = re.search(restr, filename)
            if match:
                base_name = match.group(1)
                num = int(match.group(2)) + 1
                filename = f"{base_name}({num}){ext}"
        input_file.filename = filename
        file = cls(filename=input_file.filename, author_id=author_id)
        folder.files.append(file)
        # author = User.query.filter_by(id=author_id).first()
        # author.dynamic_info.files.append(file)
        if tags is not None:
            file.tags = tags
        db.session.add(file)
        db.session.commit()
        input_file.save(file.PATH)
        return file

    def html_form(self):
        return f"""
        <li class='file-item'>
            <span class='file-icon'>📄
                <span class='file'>{self.filename}
                
                    <form method='POST'>
                        <input type='hidden' name='action' value='download'>
                        <input type='hidden' name='file_id' value='{self.id}'>
                        <button type='submit' class='delete-btn'>🔗</button>    
                    </form>
                    
                    <form method='POST' action='/file/delete/' style='display: inline-block;'>
                        <input type='hidden' name='file_id' value='{self.id}'>
                        <input type='hidden' name='user_id' value='{self.author_id}'>
                        <button type='submit' class='delete-btn'>🗑️</button>
                    </form>
                </span>
            </span>
        </li>
        """


class Folder(db.Model):
    __tablename__ = 'folder'
    id = db.Column(db.Integer, primary_key=True)
    folder_name = db.Column(db.String(150), nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    # parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    parent_folders = db.relationship(
        'Folder', secondary=folder_folder_association,
        primaryjoin=(folder_folder_association.c.child_folder_id == id),
        secondaryjoin=(folder_folder_association.c.parent_folder_id == id),
        backref='child_folders'
    )
    # children = db.relationship(
    #     'Folder', backref=db.backref('parent', remote_side=[id]),
    #     cascade='all, delete-orphan'
    # )
    # parent = db.relationship(
    #     'Folder', backref=db.backref('children', remote_side=[id]),
    #     remote_side=[id], cascade='all, delete-orphan'
    # )
    # files = db.relationship(
    #     'File', backref='folder', lazy=True,
    #     cascade='all, delete-orphan'
    # )
    cite_times = db.Column(db.Integer, default=1)

    # @property
    # def PATH(self) -> str:
    #     path = []
    #     current_folder = self
    #     while current_folder is not None:
    #         path.append(current_folder.folder_name)
    #         current_folder = current_folder.parent
    #     path = '/'.join(reversed(path))
    #     author = User.query.filter_by(id=self.author_id).first()
    #     path = os.path.join(Config.UPLOAD_FOLDER(author.uid), path)
    #     return path

    def delete(self):
        for child in self.children:
            child.delete()
        for file in self.files:
            file.delete()
        self.decrease_cite_times()

    def decrease_cite_times(self):
        self.cite_times -= 1
        if self.cite_times == 0:
            db.session.delete(self)
        db.session.commit()

    def increase_cite_times(self):
        self.cite_times += 1
        db.session.commit()
        for child in self.children:
            child.increase_cite_times()
        for file in self.files:
            file.increase_cite_times()

    def rename(self, new_folder_name):
        # os.rename(self.PATH, new_folder_name)
        self.folder_name = new_folder_name
        db.session.commit()

    # def move(self, new_folder):
    #     shutil.move(
    #         self.PATH,
    #         new_folder.PATH + '/' + self.folder_name
    #     )
    #     self.parent.children.remove(self)
    #     new_folder.children.append(self)
    #     self.parent = new_folder
    #     db.session.commit()

    @classmethod
    def copy(cls, obj, target_folder):
        obj.increase_cite_times()
        target_folder.children.append(obj)
        obj.parent_folders.append(target_folder)
        db.session.commit()

    @classmethod
    def create(cls, folder_name, parent_folder, author_id):
        # print(f"folder_name: {folder_name}, parent_id: {parent_id}, author_id: {author_id}")
        if parent_folder is not None:
            if parent_folder.check_has_folder(folder_name):
                i = 1
                while parent_folder.check_has_folder(f"{folder_name}({i})"):
                    i += 1
                folder_name = f"{folder_name}({i})"
        folder = cls(folder_name=folder_name, author_id=author_id)
        if parent_folder is not None:
            parent_folder.child_folders.append(folder)
            # folder.parent_folders.append(parent_folder)
        db.session.add(folder)
        db.session.commit()
        # os.makedirs(folder.PATH, exist_ok=True)
        return folder

    def check_has_file(self, filename):
        for file in self.files:
            if file.filename == filename:
                return True
        return False

    def check_has_folder(self, folder_name):
        for folder in self.child_folders:
            if folder.folder_name == folder_name:
                return True
        return False

    # @property
#     def to_html(self, cnt=0):
#         # html = f"<li><span class='filelist'><button id='folderBtn'>{self.folder_name}</button></span><ul>"
#         html = (f"""
# <li>
#     <span class='folderButtonList'><label for='folderBtn'>{self.folder_name}</label>
#         <form method="POST" id="folderForm{cnt}">
#             <input type="hidden" name="folder_name" value="">
#             <input type="hidden" name="parent_id" value="{self.id}">
#             <input type="hidden" name="author_id" value="{self.author_id}">
#             <select name="action">
#                 <option value="upload">上传文件</option>
#                 <option value="new_folder">新建文件夹</option>
#             </select>
#             <input type="submit" value="确定">
#         </form>
#     </span>
#     <ul class='filelist'>
#         """)
#         for child_folder in self.children:
#             cnt += 1
#             html_, cnt_ = child_folder.to_html(cnt)
#             html += html_
#             cnt = cnt_
#         html += "</ul>"
#         # html += '<br>'
#         html += "<ul class='filelist'>"
#         for file in self.files:
#             html += file.to_html
#         # html += "</ul>"
#         html += "</ul></li>"
#         return html, cnt

    def download(self):
        ...

    def html_code(self, cnt=0):
        html = (f"""
    <span class='folderButtonList'>
        <label for='folderBtn'>📁</label>
        <form method="POST">
            <input type="hidden" name="action" value="parent_folder">
            <input type="hidden" name="folder_id" value="{self.id}">
            <button type="submit" class="folder-btn">...</button>
        </form>
    </span>
<li>
    <span class='folderButtonList'>
        <label for='folderBtn'>📁{self.folder_name}</label>
        <form method="POST" id="folderForm"> 
            <input type="hidden" name="folder_name" value="">
            <input type="hidden" name="parent_id" value="{self.id}">
            <input type="hidden" name="user_id" value="{self.author_id}">
            <select name="action">
                <option value="upload">上传文件</option>
                <option value="new_folder">新建文件夹</option>
            </select>
            <input type="submit" value="确定">
        </form>
    </span>
    <ul class='filelist'>
        """)
        for child_folder in self.child_folders:
            html_, cnt_ = child_folder.folder_form(cnt)
            html += html_
            cnt = cnt_
        html += "</ul>"
        html += "<ul class='filelist'>"
        for file in self.files:
            html += file.html_form()
        html += "</ul></li>"
        return html

    def html_form(self):
       return f"""
        <li class='file-item'>
            <span class='file-icon'>📄
                <span class='file'>{self.folder_name}
                    <form method='POST' action='/file/delete/' style='display: inline-block;'>
                        <input type='hidden' name='file_id' value='{self.id}'>
                        <button type='submit' class='delete-btn'>🗑️</button>
                    </form>
                </span>
            </span>
        </li>
        """

    def folder_form(self, cnt):
        html_folder_form= f"""
        <li class='file-item'>
            <span class='file-icon'>📁
                
                    <form method='POST' style='border: none; display: inline-block;'>
                        <input type='hidden' name='action' value='subfolder'>
                        <input type='hidden' name='folder_id' value='{self.id}'>
                        <input type='hidden' name='user_id' value='{self.author_id}'>
                        
                        <button type='submit' class='folder-btn'>{self.folder_name}</button>
                    </form>
                    
            
                
            </span>
        </li>
        """
        return html_folder_form, cnt+1


# 自动维护自增的 uid
@event.listens_for(User, 'before_insert')
def receive_before_insert(mapper, connection, target):
    max_uid = db.session.query(db.func.max(User.uid)).scalar()
    if max_uid is None:
        max_uid = 100000  # 如果表为空，设置初始值为 99999
    target.uid = max_uid + 1
