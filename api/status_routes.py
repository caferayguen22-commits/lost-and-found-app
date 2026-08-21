from flask import Blueprint, render_template

from services.db import items_collection

status_bp = Blueprint('status', __name__)


@status_bp.route('/status/<tracking_code>')
def check_status(tracking_code):
    item = items_collection.find_one({"tracking_code": tracking_code})
    if not item:
        return render_template('status.html', found=False), 404
    item['_id'] = str(item['_id'])
    return render_template('status.html', found=True, item=item)
