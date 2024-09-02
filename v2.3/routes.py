from typing import Any

from flask import render_template, redirect, url_for, flash, request, session, jsonify, abort
from werkzeug.utils import secure_filename, send_from_directory
import os
from app import app, db
from models import User, File, UserDynamicInfo, UserStaticInfo, Folder
from datetime import datetime
from config import Config
import markdown2
# from flask import send_from_directory


@app.route('/')
def index():
    session.clear()
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # print("here login")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = UserDynamicInfo.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            user = User.query.get_or_404(user.user_id)
            user.static_info.login()
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
        confirm_password = request.form['confirm_password']
        if not username.isalnum() or not password.isalnum():
            flash('用户名和密码只能包含字母和数字')
        elif not (any(char.isdigit() for char in password) and any(char.isalpha() for char in password)):
            flash('密码必须同时包含字母和数字')
        elif not 6 <= len(password) <= 18:
            flash('密码长度必须大于等于6位小于等于18位')
        elif password != confirm_password:
            flash('两次输入的密码不一致')
        elif User.check_username_exist(username):
            flash('该用户名已被注册')
        else:
            User.register(username, password)
            # user = User(username=username)
            # user.set_password(password)
            # db.session.add(user)
            # db.session.commit()
            flash('注册成功，请登录')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile(user_id):
    # print("here profile")
    user = User.query.get_or_404(user_id)
    # 读取/static/extras/user.uid/BIO.txt文件，并渲染为markdown
    user_bio_markdown = ""
    with open(os.path.join(app.static_folder, 'extras', str(user.uid), 'BIO.txt'), 'r', encoding='utf-8') as f:
        user_bio_markdown = f.read()

    user_bio_markdown = markdown2.markdown(user_bio_markdown)
    # user_bio_markdown = markdown2.markdown(user.bio or "这个用户还没有填写个人简介")
    ##########################################
    logged_in_user_id = session.get('user_id')
    if logged_in_user_id != user_id:
        # 如果不是，阻止修改并仅显示信息
        if request.method == 'POST':
            flash('您无权修改此用户的信息')
            return redirect(url_for('profile', user_id=user_id))
        return render_template('profile.html', user=user, can_edit=False, bio_markdown=user_bio_markdown)
    ##################################################################
    username = request.form.get('username')
    password = request.form.get('password')
    real_name = request.form.get('real_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    student_id = request.form.get('student_id')
    user.update_info(
        username=username, password=password, real_name=real_name, email=email,
        phone=phone, student_id=student_id
    )
    ##################################################################
    return render_template('profile.html', user=user,
                           can_edit=True, img_path=f'extras/{user.uid}/IMG.png', bio_markdown=user_bio_markdown)


@app.route('/revise_info/<int:user_id>', methods=['GET', 'POST'])
def revise_info(user_id):
    # print("here revise_user_info")
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        real_name = request.form.get('real_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        student_id = request.form.get('student_id')
        user.update_info(
            username=username, password=password, real_name=real_name,
            email=email, phone=phone, student_id=student_id
        )
        flash('信息修改成功')
        return redirect(url_for('profile', user_id=user.id))
    return render_template('revise_info.html', user=user)


@app.route('/user_filelist/<int:user_id>,<int:subfolder_id>', methods=['GET', 'POST'])
def user_filelist(user_id, subfolder_id=0):
    # print("here user_filelist")
    user = User.query.get_or_404(user_id)
    # file_html, script = user.to_html
    if request.method == 'POST':
        action = request.form.get('action')
        # flash(f'执行{action}操作成功')
        if action == 'upload':  # 上传文件
            parent_id = request.form.get('parent_id')
            # print(parent_id)
            return redirect(url_for('upload', parent_id=parent_id))
        elif action == 'new_folder':  # 创建文件夹
            folder_name = request.form.get('folder_name')
            if folder_name == '':
                flash('文件夹名不能为空')
                return redirect(request.url)
            parent_folder_id = request.form.get('parent_id')
            parent_folder = Folder.query.get(parent_folder_id)
            Folder.create(folder_name, parent_folder, user_id)
            flash('文件夹创建成功')
            return render_template('user_filelist.html', user=user, files=parent_folder.html_code())
        elif action == 'download':  # 下载文件
            file_id = request.form.get('file_id')
            file = File.query.get_or_404(file_id)
            lis = [parent.id for parent in file.folders]
            if len(lis) == 1:
                parent_folder_id = lis[0]
            else:
                parent_folder_id = 0
            file.download()
            filepath = rf'E:\Web Project\WEB\v2.3\files\ '
            flash(filepath)
            return send_from_directory(filepath, file.filename, as_attachment=True, environ=request.environ)
            # return redirect(url_for('user_filelist', user_id=user.id, subfolder_id=parent_folder_id))
        elif action == 'subfolder':  # 进入子文件夹
            folder_id = request.form.get('folder_id')
            folder = Folder.query.get(folder_id)
            return render_template('user_filelist.html', user=user, files=folder.html_code())
        elif action == 'parent_folder':   # 返回上一级文件夹
            folder_id = request.form.get('folder_id')
            folder = Folder.query.get(folder_id)
            if folder.parent_folders is None:
                return redirect(url_for('user_filelist', user_id=user.id, files=user.html_code()))
            else:
                lis = [parent.id for parent in folder.parent_folders]
                if len(lis) == 1:
                    parent_folder_id = lis[0]
                    return redirect(url_for('user_filelist', user_id=user.id, subfolder_id=parent_folder_id))
                else:
                    return redirect(url_for('user_filelist', user_id=user.id, subfolder_id=subfolder_id))

    if subfolder_id == 1:
        return render_template('user_filelist.html', user=user, files=user.html_code())
    else:
        subfolder = Folder.query.get(subfolder_id)
        return render_template('user_filelist.html', user=user, files=subfolder.html_code())


@app.route('/upload/<int:parent_id>', methods=['GET', 'POST'])
def upload(parent_id):
    # print("here upload")
    # flash(parent_id)
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('未选择文件')
            return redirect(request.url)
        file = request.files['file']
        if not file:
            flash('未选择文件')
            return redirect(request.url)
        if file.filename == '':
            flash('未选择文件')
            return redirect(request.url)
        if file:
            # filename = secure_filename(file.filename)
            user_id = session.get('user_id')
            user = User.query.get_or_404(user_id)
            # parent_id = request.form.get('parent_id')
            # print('upload', parent_id)
            user.upload(file, parent_id)
            flash('文件上传成功')
            
            flash(parent_id)
            return redirect(url_for('user_filelist', user_id=user.id, subfolder_id=parent_id))
    return render_template('upload.html', parent_id=request.args.get('parent_id'))

#
# @app.route('/user_filelist/<int:file_id>')
# def download(file_id):
#     # print("here download")
#     file = File.query.get_or_404(file_id)
#     file.download()
#     filepath = rf"E:\Web Project\WEB\v2.3\files\{file_id}"
#     flash(filepath)
#     # # 输出文件的绝对路径
#     # return send_from_directory(app.config['UPLOAD_FOLDER'], file.filename, as_attachment=True,
#     #                            environ=request.environ)
#     return send_from_directory(filepath, file.filename, as_attachment=True,
#                                environ=request.environ)
#     # filepath = file.PATH
#     # try:
#     #     # 检查文件是否存在
#     #     if not os.path.isfile(os.path.join(filepath, file.filename)):
#     #         abort(404)  # 文件未找到
#     #
#     #     # 发送文件
#     #     send_from_directory(filepath, file.filename, as_attachment=True, environ=request.environ)
#     #     flash("error")
#     #     return redirect(url_for('user_filelist', user_id=file.author_id, subfolder_id=file.id))
#     # except Exception as e:
#     #     # 捕获任何其他异常并返回500错误
#     #     return str(e), 500


@app.route('/search', methods=['GET', 'POST'])
def search():
    # print("here search")
    if request.method == 'POST':
        search_type = request.form.get('search_type')
        query = request.form.get('query')
        results = []
        if search_type == 'user':
            results = User.query.filter(User.contains(query)).all()
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
        # username = user.dynamic_info.username
        # flash(f'已成功删除{username}')
        user.delete()
        # return redirect(url_for('login'))

    return render_template('delete_account.html', user=user)


@app.route('/extras/<int:user_id>', methods=['GET', 'POST'])
def change_img(user_id):
    # print("here change_img")
    # user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # 验证文件类型
            if not file.filename.endswith(tuple(Config.IMG_ALLOWED_EXTENSIONS)):
                flash('图片格式不正确')
                return redirect(request.url)
            # 保存文件到指定目录
            user.change_img(file)
            # filename = secure_filename(file.filename)
            # filepath = os.path.join(app.config['IMG_FOLDER'], filename)
            # file.save(filepath)
            # user.img_path = os.path.join('img', filename)
            # db.session.commit()
            flash('头像更改成功')
        else:
            flash('未选择文件')
    return redirect(url_for('profile', user_id=user.id))


# 写一个修改用户密码的接口
@app.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
def change_password(user_id):
    # print("here change_password")
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        if not user.dynamic_info.check_password(old_password):
            flash('旧密码错误')
            return redirect(request.url)
        msg = user.update_info(password=new_password)
        flash(msg)
        return redirect(url_for('profile', user_id=user.id))
        # if not (any(char.isdigit() for char in new_password) and any(char.isalpha() for char in new_password)):
        #     flash('密码必须同时包含字母和数字')
        # elif not 6 <= len(new_password) <= 18:
        #     flash('密码长度必须大于等于6位小于等于18位')
        # else:
        #     user.set_password(new_password)
        #     db.session.commit()
        #     flash('密码修改成功')
        #     return redirect(url_for('profile', user_id=user.id))

    return render_template('change_password.html', user=user)


@app.route('/manage_users/<int:user_id>', methods=['GET', 'POST'])
def manage_users(user_id):
    # 获取所有用户
    user = User.query.get_or_404(user_id)
    users = User.query.all()
    return render_template('all_users.html', user=user, users=users, img_path=f'extras/{user.uid}/IMG.png')


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json()
    user_id = data.get('user_id')
    user = User.query.get(user_id)
    if user:
        user.last_active = datetime.utcnow()
        db.session.commit()
    return '', 204


def check_user_timeout():
    # 检查用户是否超时（如10分钟）
    timeout = datetime.utcnow() - datetime.timedelta(minutes=10)
    offline_users = User.query.filter(User.last_active < timeout).all()
    for user in offline_users:
        user.online = False
        db.session.commit()

    return offline_users


@app.route('/guest_login')
def guest_login():
    # 设置游客标记
    session['guest'] = True
    session['user_id'] = None  # 游客没有用户ID
    return redirect(url_for('index'))  # 重定向到主页或其他页面


@app.route('/logout')
def logout():
    # 退出登录
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        user.logout()
        db.session.commit()

    session.clear()

    return redirect(url_for('index'))  # 重定向到主页或其他页面


@app.route('/base')
def base():
    return render_template('base.html')


@app.route('/all_users/<int:user_id>', methods=['POST'])
def change_user_permission(user_id):
    user = User.query.get(user_id)
    each_user_id = request.form.get('each_user_id', type=int)
    in_or_de = request.form.get('inORde', type=str)

    if each_user_id is None:
        flash('用户不存在')
        return redirect(url_for('manage_users', user_id=user_id))
    each_user = User.query.get(each_user_id)
    if each_user.static_info.permission_level < user.static_info.permission_level:
        if in_or_de == 'de':
            each_user.static_info.permission_level -= 1
            flash(f'用户{each_user.dynamic_info.username}权限降低成功')
        elif in_or_de == 'in':
            each_user.static_info.permission_level += 1
            flash(f'用户{each_user.dynamic_info.username}权限提升成功')
        db.session.commit()
    else:
        flash('权限修改失败，权限等级不足')

    return redirect(url_for('manage_users', user_id=user_id))


@app.route('/update_bio/<int:user_id>', methods=['POST'])
def update_bio(user_id):
    user = User.query.get(user_id)
    user_bio_markdown = ""
    with open(os.path.join(app.static_folder, 'extras', str(user.uid), 'BIO.txt'), 'r', encoding='utf-8') as f:
        user_bio_markdown = f.read()

    user_bio_markdown = request.form.get('user_bio_markdown', user_bio_markdown)

    with open(os.path.join(app.static_folder, 'extras', str(user.uid), 'BIO.txt'), 'w', encoding='utf-8') as f:
        f.write(user_bio_markdown)
    flash('个人简介更新成功')
    return redirect(url_for('profile', user_id=user.id))


# 删除文件
@app.route('/file/delete/', methods=['POST'])
def delete_file():
    if request.method == 'POST':
        file_id = request.form.get('file_id')
        if file_id is None:
            flash('文件不存在')
            return redirect(request.url)
        file = File.query.get(file_id)
        user_id = file.author_id
        if file is None:
            flash('文件不存在')
            return redirect(request.url)
        file.delete()
        flash('文件删除成功')
    return redirect(url_for('user_filelist', user_id=user_id))

