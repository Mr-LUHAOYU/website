import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    IMG_FOLDER = 'static/img'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
