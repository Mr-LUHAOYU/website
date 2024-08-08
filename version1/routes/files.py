from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory
from Models.models import db, File, UploadRecord, UserDynamic, DownloadRecord, User, app
from flask_login import login_required, current_user
import os

files_bp = Blueprint('files', __name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}


@files_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)
            filepath = os.path.join(user_folder, file.filename)
            file.save(filepath)
            new_file = File(user_id=current_user.id, loc=filepath, fname=file.filename, tag=request.form['tag'])
            db.session.add(new_file)
            db.session.commit()
            upload_record = UploadRecord(user_id=current_user.id, file_id=new_file.id)
            db.session.add(upload_record)
            user_dynamic = UserDynamic.query.filter_by(user_id=current_user.id).first()
            user_dynamic.total_submissions += 1
            db.session.commit()
            flash('File successfully uploaded')
            return redirect(url_for('files.upload'))
        else:
            flash('Allowed file type is pdf')
    return render_template('upload.html')


@files_bp.route('/downloads/<int:user_id>/<filename>')
@login_required
def download_file(user_id, filename):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
    return send_from_directory(user_folder, filename, as_attachment=True)


@files_bp.route('/browse')
@login_required
def browse():
    users = User.query.all()
    return render_template('browse.html', users=users)


@files_bp.route('/user_files/<int:user_id>')
@login_required
def user_files(user_id):
    files = File.query.filter_by(user_id=user_id).all()
    return render_template('user_files.html', files=files, user_id=user_id)
