import datetime
import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    TIME_DELTA = datetime.timedelta(hours=8)
    # UPLOAD_FOLDER = 'static/uploads'
    # IMG_FOLDER = 'static/img'
    IMG_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    LOCAL_PATH = rf'/WEB/files/'

    @staticmethod
    def ROOT_PATH(uid):
        return f"static/uploads/{uid+100000}"

    @staticmethod
    def UPLOAD_FOLDER(uid):
        return f"files{uid+100000}"

    @staticmethod
    def IMG_PATH(uid):
        return f"extras/{uid+100000}/IMG.png"

    @staticmethod
    def BIO_PATH(uid):
        return f"extras/{uid+100000}/BIO.txt"

    @staticmethod
    def FILE_PATH(uid):
        return f"files/{uid}"

def validate_password(password):
    if not 6 <= len(password) <= 18:
        return False, "密码长度必须大于等于6位小于等于18位"
    if not any(char.isdigit() for char in password):
        return False, "密码必须同时包含字母和数字"
    if not any(char.isalpha() for char in password):
        return False, "密码必须同时包含字母和数字"
    return True, "密码修改成功"
