# api/moderation.py
from flask import Blueprint, request, jsonify
from database import get_db_connection
from api.middleware import token_required, admin_required  # Import both guards

moderation_bp = Blueprint('moderation', __name__)


@moderation_bp.route('/report', methods=['POST'])
@token_required
def report_comment(current_user):
    """Allows any logged-in user to flag a comment"""
    data = request.get_json()
    comment_id = data.get("comment_id")
    reason = data.get("reason")

    # We now pull the reporter_id dynamically from the token!
    reporter_id = current_user['user_id']

    if not comment_id or not reason:
        return jsonify({"status": "error", "message": "Missing info"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO reports (comment_id, reporter_id, reason) VALUES (?, ?, ?)',
        (comment_id, reporter_id, reason)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Report submitted"}), 201


@moderation_bp.route('/reports', methods=['GET'])
@token_required
@admin_required  # Only admins can see the list of reports
def get_pending_reports(current_user):
    """Admin Dashboard: View all pending reports"""
    conn = get_db_connection()
    reports = conn.execute("SELECT * FROM reports WHERE status = 'pending'").fetchall()
    conn.close()

    return jsonify({"status": "success", "data": [dict(r) for r in reports]}), 200


@moderation_bp.route('/action/<int:report_id>', methods=['DELETE'])
@token_required
@admin_required  # Only admins can take action (delete & strike)
def action_report(current_user, report_id):
    """Admin Action: Deletes comment and issues a strike"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find report and comment info
    report = cursor.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
    if not report:
        return jsonify({"status": "error", "message": "Report not found"}), 404

    comment = cursor.execute('SELECT * FROM comments WHERE id = ?', (report['comment_id'],)).fetchone()
    if not comment:
        return jsonify({"status": "error", "message": "Comment not found"}), 404

    # The 3-Strike Logic
    author_id = comment['author_id']
    cursor.execute('DELETE FROM comments WHERE id = ?', (report['comment_id'],))
    cursor.execute("UPDATE reports SET status = 'resolved' WHERE id = ?", (report_id,))
    cursor.execute('UPDATE users SET strike_count = strike_count + 1 WHERE id = ?', (author_id,))

    # Check for auto-ban
    user = cursor.execute('SELECT strike_count FROM users WHERE id = ?', (author_id,)).fetchone()
    if user and user['strike_count'] >= 3:
        cursor.execute("UPDATE users SET status = 'blocked' WHERE id = ?", (author_id,))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Action completed"}), 200