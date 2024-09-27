from flask import render_template, redirect, url_for, flash, request, session, make_response, jsonify
from werkzeug.utils import send_from_directory, send_file
from app import app, db
# from models import User, File, UserDynamicInfo, UserStaticInfo, Folder, Comment
from Model3 import *
from datetime import datetime
from config import Config, validate_password
import markdown2
from sqlalchemy.orm import joinedload
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
        user = User.login(username, password)
        if user:
            session['user_id'] = user.id
            # 更新登录时间
            user.update_last_login_time()

            return redirect(url_for('playground', user_id=user.id))
        else:
            flash('账号或密码错误')
    return render_template('login-register.html')


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
        elif User.query.filter_by(username=username).first() is not None:
            flash('该用户名已被注册')
        else:
            User.register(username, password)
            flash('注册成功，请登录')
            return redirect(url_for('login'))
    return render_template('login-register.html')


@app.route('/login-register', methods=['GET', 'POST'])
def login_register():
    # print("here login_register")
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'login':
            return redirect(url_for('login'))
        elif action == 'register':
            return redirect(url_for('register'))
    return render_template('login-register.html')


@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile(user_id):
    # print("here profile")
    user = User.query.get_or_404(user_id)
    # 读取/static/extras/user.uid/BIO.txt文件，并渲染为markdown
    user_bio_markdown = ""
    with open(f'static/extras/{user.id+100000}/BIO.txt', 'r', encoding='utf-8') as f:
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
    path = str(f'extras/{user.id+100000}/IMG.png')
    ##################################################################
    return render_template('profile.html', user=user, can_edit=True, img_path=path,  bio_markdown=user_bio_markdown, pic_path="niubo")


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


@app.route('/user_filelist/<int:user_id>,<int:current_folder_id>', methods=['GET', 'POST'])
def user_filelist(user_id, current_folder_id=1):
    current_user_id = session.get('user_id')
    current_user = User.query.get(current_user_id)
    # print("here user_filelist")
    user = User.query.get_or_404(user_id)
    # file_html, script = user.to_html
    if request.method == 'POST':
        action = request.form.get('action')
        # flash(f'执行{action}操作成功')
        if action == 'upload':  # 上传文件
            target_folder_id = request.form.get('current_folder_id')
            # print(parent_id)
            return redirect(url_for('upload', target_folder_id=target_folder_id))
        elif action == 'new_folder':  # 创建文件夹
            folder_name = request.form.get('folder_name')
            if folder_name == '':
                flash('文件夹名不能为空')
                return redirect(request.url)
            elif Folder.query.filter_by(name=folder_name, owner_id=user.id).first() is not None:
                flash('文件夹名已存在')
                return redirect(request.url)
            current_folder_id = request.form.get('current_folder_id')
            current_folder = Folder.query.get(current_folder_id)
            Folder.create(folder_name, user_id, current_folder_id)
            flash('文件夹创建成功')

        elif action == 'download':  # 下载文件
            file_id = request.form.get('file_id')
            return download(file_id)
            # file = File.download(file_id)
            # filepath = Config.FILE_PATH(file_id)
            # # 将path转为绝对路径
            # filepath = os.path.abspath(filepath)
            # if not os.path.exists(filepath):
            #     flash('文件不存在')
            #     return redirect(request.url)
            # if file is None:
            #     flash('文件不存在')
            #     return redirect(request.url)
            # print("YES")
            # # flash(filepath)
            # # 创建响应对象
            # response = make_response(
            #     send_from_directory(filepath, file_id, as_attachment=True, environ=request.environ))
            #
            # print("OK")
            # # 设置新的文件名
            # new_filename = file.name.encode('utf-8', 'replace').decode('latin-1')
            # response.headers["Content-Disposition"] = f"attachment; filename={new_filename}"
            # return response

        elif action == 'subfolder':  # 进入子文件夹
            folder_id = request.form.get('folder_id')
            folder = Folder.query.get(folder_id)
            current_folder_id = folder.id

        elif action == 'parent_folder':   # 返回上一级文件夹
            current_folder_id = request.form.get('current_folder_id')
            current_folder = Folder.query.get(current_folder_id)
            if current_folder and current_folder.parent_folders:
                parent_folder_id = current_folder.parent_folders[0].id
                current_folder_id = parent_folder_id
            files = current_folder.files
            return redirect(url_for('user_filelist', user_id=user.id, current_folder_id=current_folder_id,
                                    files=files, current_user=current_user))
    if current_folder_id == 1:
        current_folder = Folder.query.filter_by(owner_id=user.id, parent_folders=None).first()
    else:
        current_folder = Folder.query.get(current_folder_id)

    files = current_folder.files
    sub_folders = current_folder.child_folders

    return render_template('user_filelist.html', user=user, current_folder=current_folder,
                           files=files, sub_folders=sub_folders, current_user=current_user)


@app.route('/upload/<int:target_folder_id>', methods=['GET', 'POST'])
def upload(target_folder_id):
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('未选择文件')
            return redirect(request.url)
        file = request.files['file']
        if not file or file.filename == '':
            flash('未选择文件')
            return redirect(request.url)
        user_id = session.get('user_id')
        user = User.query.get_or_404(user_id)
        # user.upload(file, parent_id)
        File.upload(target_folder_id, user_id, file)
        flash('文件上传成功')

        # flash(target_folder_id)
        return redirect(url_for('user_filelist', user_id=user.id, current_folder_id=target_folder_id))
    return render_template('upload.html', target_folder_id=request.args.get('parent_id'))


# TODO: 传递文件对象而非文件路径
@app.route('/download/<string:file_id>')
def download(file_id):
    # file = File.query.get_or_404(file_id)
    file_stream, filename = File.download(file_id)
    # filepath = Config.FILE_PATH(file_id)
    # 将path转为绝对路径
    # filepath = os.path.abspath(filepath)
    # flash(filepath)
    # 创建响应对象
    response = make_response(
        send_file(
            file_stream, download_name=filename,
            as_attachment=True, environ=request.environ
        )
    )
    # 设置新的文件名
    # new_filename = file.name.encode('utf-8', 'replace').decode('latin-1')
    # response.headers["Content-Disposition"] = f"attachment; filename={new_filename}"

    return response


# TODO: 没看懂
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
            results = File.query.filter(File.name.contains(query)).order_by(File.name.desc()).all()
        # print(results)
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
        # if not user.check_password(old_password):
        if user.password != old_password:
            flash('旧密码错误')
            return redirect(request.url)
        flag, msg = validate_password(new_password)
        flash(msg)
        if flag:
            user.set_password(new_password)
        return redirect(url_for('profile', user_id=user.id))

    return render_template('change_password.html', user=user)


@app.route('/manage_users/<int:user_id>', methods=['GET', 'POST'])
def manage_users(user_id):
    # 获取所有用户
    user = User.query.get_or_404(user_id)
    users = User.query.all()
    return render_template('all_users.html', user=user, users=users)


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


@app.route('/update_bio/<int:user_id>', methods=['POST'])
def update_bio(user_id):
    user = User.query.get(user_id)
    user_bio_markdown = ""
    path = Config.BIO_PATH(user.id)
    with open(f'static/{path}', 'r', encoding='utf-8') as f:
        user_bio_markdown = f.read()

    user_bio_markdown = request.form.get('user_bio_markdown', user_bio_markdown)

    with open(f'static/{path}', 'w', encoding='utf-8') as f:
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
        folder_id = file.parent_folders[0].id
        user_id = file.owner_id
        user = User.query.get_or_404(user_id)
        if file is None:
            flash('文件不存在')
            return redirect(request.url)
        file.delete()
        flash('文件删除成功')
        return redirect(url_for('user_filelist', user=user, user_id=user.id, current_folder_id=folder_id))
    return redirect(request.url)


# 用户广场
@app.route('/playground', methods=['GET', 'POST'])
def playground():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    # 获取当前时间
    date = datetime.now().date()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'upload':  # 上传文件
            # TODO
            ...
        elif action == 'grade':  # 成绩查询
            # TODO
            ...
        elif action == 'homework':  # 作业查询
            # TODO
            ...
        elif action == 'profile':  # 个人主页
            # TODO
            ...
        elif action == 'download':  # 下载文件
            file_id = request.form.get('file_id')
            file = File.query.get_or_404(file_id)
            file.download()
            filepath = Config.FILE_PATH(file_id)
            # 将path转为绝对路径
            filepath = os.path.abspath(filepath)
            flash(filepath)
            # 创建响应对象
            response = make_response(
                send_from_directory(filepath, file_id, as_attachment=True, environ=request.environ))

            # 设置新的文件名
            new_filename = file.name.encode('utf-8', 'replace').decode('latin-1')
            response.headers["Content-Disposition"] = f"attachment; filename={new_filename}"

            return response
        elif action == 'comment':  # 评论
            file_id = request.form.get('file_id')
            author_id = request.form.get('author_id')
            comment_content = request.form.get('comment')

            comment = Comment(content=comment_content, author_id=author_id, file_id=file_id)
            db.session.add(comment)
            db.session.commit()

    # 列出所有文件,然后按上传时间排序
    files = File.query.order_by(File.uploaded_on.desc()).all()
    # 列出所有用户，以字典形式返回，key为id，value为用户名
    users = {user.id: user.username for user in User.query.all()}
    # # 列出所有文件的评论，以字典形式返回，key为file_id，value为评论列表
    # comments = {file.id: file.comment for file in files}
    # 获取所有post对象，以及每个post对应的owner，以元组形式返回，key为post_id，value为元组(owner, post)
    posts = [(post.id, (User.query.get(post.owner_id), post)) for post in Post.query.all()]
    return render_template('playground.html', date=date, files=files, users=users, user=user,
                           user_id=user_id, posts=posts)


@app.route('/create_post/<int:user_id>', methods=['GET', 'POST'])
def create_post(user_id):
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        user_id = session.get('user_id')
        user = User.query.get_or_404(user_id)

        folder_name = title.replace(' ', '_')
        if Folder.query.filter_by(name=folder_name, owner_id=user.id).first() is not None:
            flash('不可使用该title，请更换')
            return redirect(request.url)
        root = Folder.query.filter_by(owner_id=user.id, parent_folders=None).first()
        folder = Folder.create(folder_name, user_id, root.id)

        post = Post(title=title, content=content, owner_id=user_id, folder_id=folder.id)
        db.session.add(post)
        db.session.commit()
        flash('帖子创建成功')
        return redirect(url_for('playground'))
    return render_template('create_post.html', user_id=user_id)


@app.route('/post_detail/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    # 获取当前帖子
    post = Post.query.get_or_404(post_id)
    # 获取帖子的作者
    author = User.query.get_or_404(post.owner_id)

    comments = Comment.query.filter_by(post_id=post_id).all()
    # 获取所有评论，以及每个评论对应的作者和文件，以元组形式返回，key为comment_id，value为元组(author, file, comment)
    comments = [(comment.id, (User.query.get(comment.owner_id), File.query.get(comment.file_id), comment)) for comment in comments]

    if request.method == 'POST':
        content = request.form.get('content')
        # print(content)
        user_id = session.get('user_id')
        user = User.query.get_or_404(user_id)
        file = request.files.get('attachment')
        if file:
            current_file = File.upload(post.folder_id, user_id, file)
            db.session.commit()
            comment = Comment(content=content, owner_id=user_id, post_id=post_id, file_id=current_file.id)
        else:
            comment = Comment(content=content, owner_id=user_id, post_id=post_id, file_id=0)
        db.session.add(comment)
        db.session.commit()

        return redirect(url_for('post_detail', post_id=post_id, author=author, comments=comments, user=user))

    return render_template('post_detail.html', post=post, author=author, comments=comments, user=user)


@app.route('/like_post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    post = Post.query.get_or_404(post_id)  # 获取帖子
    user_id = session.get('user_id')  # 获取当前用户ID
    user = User.query.get_or_404(user_id)  # 获取当前用户对象
    is_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()  # 获取所有点赞该帖子的用户
    # 判断当前用户是否已经点赞过该帖子
    if is_like:
        db.session.delete(is_like)  # 删除点赞对象
        post.likes -= 1  # 减少点赞数
    else:
        like = Like(user_id=user_id, post_id=post_id, comment_id=0)  # 创建点赞对象
        db.session.add(like)  # 添加到数据库
        post.likes += 1  # 增加点赞数
    db.session.commit()  # 提交到数据库
    return jsonify({'likes': post.likes, 'liked':  is_like is None})  # 返回新的点赞数及点赞状态


@app.route('/admin/<int:user_id>', methods=['GET', 'POST'])
def admin(user_id):
    current_user = User.query.get_or_404(session.get('user_id'))
    # if current_user.is_admin is False:
    #     flash('无权限访问')
    #     return redirect(url_for('index'))
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            user_id = request.form.get('user_id')
            user = User.query.get_or_404(user_id)
            user.delete()
            flash(f'用户{user.username}已删除')
            return redirect(url_for('admin_users'))
    users = User.query.all()
    return render_template('admin.html', user=current_user, users=users)


@app.route('/admin_manage_users', methods=['GET', 'POST'])
def admin_manage_users():
    users = User.query.all()
    return render_template('admin_manage_users.html', users=users)


@app.route('/admin_revise_user_info/<int:user_id>', methods=['GET', 'POST'])
def admin_revise_user_info(user_id):
    # print("here revise_user_info")
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        real_name = request.form.get('real_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        student_id = request.form.get('student_id')
        is_admin = request.form.get('is_admin') == '1'
        print(is_admin)
        user.update_info(
            username=username, password=password, real_name=real_name,
            email=email, phone=phone, student_id=student_id, is_admin=is_admin
        )
        flash('信息修改成功')
        return redirect(url_for('admin', user_id=user.id))
    return render_template('admin_revise_user_info.html', user=user)


@app.route('/admin_delete_user/<int:user_id>', methods=['GET', 'POST'])
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    # if request.method == 'POST':
    user.delete()
    flash(f'用户{user.username}已删除')
    print(user.username)
    # return redirect(url_for('admin_users'))
    # return render_template('admin.html', user=user)
    return redirect(url_for('admin_manage_users'))


@app.route('/admin_manage_files', methods=['GET', 'POST'])
def admin_manage_files():
    files = File.query.all()
    return render_template('admin_manage_files.html', files=files)


@app.route('/admin_download_file', methods=['GET', 'POST'])
def admin_download_file():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'download':
            file_id = request.form.get('file_id')
            return download(file_id)


@app.route('/admin_delete_file', methods=['GET', 'POST'])
def admin_delete_file():
    if request.method == 'POST':
        action = request.form.get('action')
        print(action)
        if action == 'delete':
            file_id = request.form.get('file_id')
            if file_id is None:
                flash('文件不存在')
                return redirect(request.url)
            file = File.query.get(file_id)
            user_id = file.owner_id
            if file is None:
                flash('文件不存在')
                return redirect(request.url)
            file.delete()
            flash('文件删除成功')
            return redirect(url_for('admin', user_id=user_id))

    return redirect(request.url)


@app.route('/admin_manage_posts', methods=['GET', 'POST'])
def admin_manage_posts():
    posts = [(post.id, (User.query.get(post.owner_id), post)) for post in Post.query.all()]
    return render_template('admin_manage_posts.html', posts=posts)


@app.route('/admin_delete_post/<int:post_id>', methods=['GET', 'POST'])
def admin_delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    user_id = post.owner_id
    post.delete()
    return redirect(url_for('admin', user_id=user_id))


@app.route('/admin_edit_post/<int:post_id>', methods=['GET', 'POST'])
def admin_edit_post(post_id):
    user_id = session.get('user_id')
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        post.update_info(title=title, content=content)
        flash('帖子修改成功')
        return redirect(url_for('admin', user_id=user_id))
    return render_template('admin_edit_post.html', post_id=post_id, post=post)


@app.route('/my_posts/<int:user_id>', methods=['GET', 'POST'])
def my_posts(user_id):
    user = User.query.get_or_404(user_id)
    posts = [(post.id, (User.query.get(post.owner_id), post)) for post in Post.query.filter_by(owner_id=user_id).all()]
    return render_template('my_posts.html', user=user, posts=posts)


@app.route('/my_comments/<int:user_id>', methods=['GET', 'POST'])
def my_comments(user_id):
    user = User.query.get_or_404(user_id)
    posts = [(post.id, (User.query.get(post.owner_id), post)) for post in Post.query.filter_by(owner_id=user_id).all()]
    return render_template('my_comments.html', user=user, posts=posts)


@app.route('/my_comments_detail/<int:post_id>', methods=['GET', 'POST'])
def my_comments_detail(post_id):
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    # 获取当前帖子
    post = Post.query.get_or_404(post_id)
    # 获取帖子的作者
    author = User.query.get_or_404(post.owner_id)

    comments = Comment.query.filter_by(post_id=post_id).all()
    # 获取这篇帖子的所有我的评论，以及每个评论对应的作者和文件，以元组形式返回，key为comment_id，value为元组(author, file, comment)
    my_comments = [(comment.id, (User.query.get(comment.owner_id), File.query.get(comment.file_id), comment)) for comment in comments if comment.owner_id == user_id]
    return render_template('my_comments_detail.html', post=post, author=author, comments=my_comments, user=user)
