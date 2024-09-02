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

    @staticmethod
    def ROOT_PATH(uid):
        return f"static/uploads/{uid}"

    @staticmethod
    def UPLOAD_FOLDER(uid):
        return f"files{uid}"

    @staticmethod
    def IMG_PATH(uid):
        return f"static/extras/{uid}/IMG.png"

    @staticmethod
    def BIO_PATH(uid):
        return f"static/extras/{uid}/BIO.txt"
