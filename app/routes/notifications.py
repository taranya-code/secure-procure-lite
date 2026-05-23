from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Notification

bp = Blueprint('notifications', __name__)


@bp.route('/notifications')
@login_required
def index():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()).all()
    # Mark all as read
    Notification.query.filter_by(user_id=current_user.id, read=False).update({'read': True})
    db.session.commit()
    return render_template('dashboard/notifications.html', notifications=notifs)
