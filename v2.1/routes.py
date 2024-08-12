from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.utils import secure_filename, send_from_directory
import os
from app import app, db
from models import User, File
from datetime import datetime


@app.route('/')
def index():
    # print("here index")
    return render_template('index.html')
    # return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # print("here login")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            user.is_logged_in = True
            user.last_login = datetime.utcnow()
            db.session.commit()
            session['user_id'] = user.id
            return redirect(url_for('profile', user_id=user.id))
        else:
            flash('账号或密码错误')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # print("here register")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username.isalnum() or not password.isalnum():
            flash('用户名和密码只能包含字母和数字')
        elif User.query.filter_by(username=username).first():
            flash('该用户名已被注册')
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('注册成功，请登录')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile(user_id):
    # print("here profile")
    user = User.query.get_or_404(user_id)
    ##########################################
    logged_in_user_id = session.get('user_id')
    if logged_in_user_id != user_id:
        # 如果不是，阻止修改并仅显示信息
        if request.method == 'POST':
            flash('您无权修改此用户的信息')
            return redirect(url_for('profile', user_id=user_id))
        return render_template('profile.html', user=user, can_edit=False)
    ##################################################################
    username = request.form.get('username')
    password = request.form.get('password')
    real_name = request.form.get('real_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    if password:
        user.set_password(password)
    if username:
        user.username = username
    if real_name:
        user.real_name = real_name
    if email:
        user.email = email
    if phone:
        user.phone = phone
    db.session.commit()
    ##################################################################
    return render_template('profile.html', user=user, can_edit=True)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    # print("here upload")
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('未选择文件')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('未选择文件')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            user_id = session.get('user_id')
            user = User.query.get_or_404(user_id)
            seri = len(user.files) + 1
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            new_file = File(user_id=user.id, seri=seri, filename=filename, filepath=filepath)
            db.session.add(new_file)
            db.session.commit()
            flash('文件上传成功')
            return redirect(url_for('profile', user_id=user.id))
    return render_template('upload.html')


@app.route('/download/<int:file_id>')
def download(file_id):
    # print("here download")
    file = File.query.get_or_404(file_id)
    file.download_count += 1
    db.session.commit()
    return send_from_directory(app.config['UPLOAD_FOLDER'], file.filename, as_attachment=True, environ=request.environ)


@app.route('/search', methods=['GET', 'POST'])
def search():
    # print("here search")
    if request.method == 'POST':
        search_type = request.form.get('search_type')
        query = request.form.get('query')
        results = []
        if search_type == 'user':
            results = User.query.filter(User.username.contains(query)).all()
        elif search_type == 'file':
            results = File.query.filter(File.filename.contains(query)).order_by(File.download_count.desc()).all()
        print(results)
        return render_template('search.html', results=results, s_type=search_type)
    return render_template('search.html')


@app.route('/delete_account/<int:user_id>', methods=['GET', 'POST'])
def delete_account(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        # 删除用户的相关数据
        db.session.delete(user)
        db.session.commit()
        flash('您的账户已被删除')
        return redirect(url_for('login'))

    return render_template('delete_account.html', user=user)
