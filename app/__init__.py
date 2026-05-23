import os
from flask import Flask
from dotenv import load_dotenv
from .extensions import db, login_manager, migrate, csrf
from .config import config

load_dotenv()


def create_app(config_name=None):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    cfg_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[cfg_name])

    # Ensure data dir exists
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'), exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to continue.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # Register blueprints
    from .routes.auth import bp as auth_bp
    from .routes.dashboard import bp as dashboard_bp
    from .routes.requests import bp as requests_bp
    from .routes.approvals import bp as approvals_bp
    from .routes.rfq import bp as rfq_bp
    from .routes.vendors import bp as vendors_bp
    from .routes.audit import bp as audit_bp
    from .routes.reports import bp as reports_bp
    from .routes.notifications import bp as notifications_bp
    from .routes.admin import bp as admin_bp
    from .routes.api import bp as api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(approvals_bp)
    app.register_blueprint(rfq_bp)
    app.register_blueprint(vendors_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Jinja2 globals
    from .utils import status_badge_class, format_currency, currency_symbol
    app.jinja_env.globals['status_badge'] = status_badge_class
    app.jinja_env.globals['fmt_currency'] = format_currency
    app.jinja_env.globals['currency_symbol'] = currency_symbol

    # Context processor: inject pending_approval_count into every template
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        count = 0
        if current_user.is_authenticated and current_user.role in ('APPROVER', 'ADMIN'):
            from .models import Approval
            count = Approval.query.filter_by(status='PENDING').count()
        return {'pending_approval_count': count}

    return app
