from flask import Blueprint, request
from flask_login import login_required, current_user
from Models.models import db, User, File, UploadRecord, DownloadRecord, UserDynamic
import os

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/clear_data', methods=['POST'])
@login_required
def clear_data():
    if not current_user.is_admin:
        return "Access denied", 403

    # Clear database records
    db.session.query(File).delete()
    db.session.query(UploadRecord).delete()
    db.session.query(DownloadRecord).delete()
    db.session.query(UserDynamic).delete()
    db.session.query(User).filter(User.id != current_user.id).delete()  # Keep current admin user
    db.session.commit()

    # Clear uploaded files
    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))

    return "All data cleared", 200
