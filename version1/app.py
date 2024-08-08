from Models.models import db
from routes.auth import auth_bp
from routes.files import files_bp
from routes.main import main_bp
from routes.admin import admin_bp
from Models.models import app

app.register_blueprint(auth_bp)
app.register_blueprint(files_bp)
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    # app.run(debug=True, host='0.0.0.0', port='5000')
