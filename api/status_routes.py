from flask import Blueprint, render_template

from services.items_repository import get_item_by_tracking_code

status_bp = Blueprint('status', __name__)


@status_bp.route('/status/<tracking_code>')
def check_status(tracking_code):
    item = get_item_by_tracking_code(tracking_code)
    if not item:
        return render_template('status.html', found=False), 404
    return render_template('status.html', found=True, item=item)
