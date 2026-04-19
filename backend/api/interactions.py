from flask import Blueprint, request, jsonify
from database import get_db_connection
from api.middleware import token_required

interactions_bp = Blueprint('interactions', __name__)


# --- 1. VOTING LOGIC ---
@interactions_bp.route('/votes', methods=['POST'])
@token_required
def cast_vote(current_user):
    data = request.get_json()
    post_id = data.get('post_id')
    vote_type = data.get('vote_type')  # 1 for Upvote, -1 for Downvote

    if not post_id or not vote_type:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    conn = get_db_connection()
    if vote_type == 1:
        conn.execute('UPDATE posts SET upvotes = upvotes + 1 WHERE id = ?', (post_id,))
        message = "Upvote recorded!"
    elif vote_type == -1:
        conn.execute('UPDATE posts SET downvotes = downvotes + 1 WHERE id = ?', (post_id,))
        message = "Downvote recorded!"

    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": message}), 200


# --- 2. ADD A REVIEW ---
@interactions_bp.route('/comments', methods=['POST'])
@token_required
def add_comment(current_user):
    data = request.get_json()
    post_id = data.get('post_id')
    content = data.get('content')

    if not post_id or not content:
        return jsonify({"status": "error", "message": "Content is required"}), 400

    conn = get_db_connection()
    # We ALWAYS save the real author_id to the database for security/admin purposes
    conn.execute(
        'INSERT INTO comments (post_id, author_id, content) VALUES (?, ?, ?)',
        (post_id, current_user['user_id'], content)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Review posted anonymously!"}), 201


# --- 3. FETCH REVIEWS (THE ANONYMITY SHIELD) ---
@interactions_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
@token_required
def get_comments(current_user, post_id):
    conn = get_db_connection()
    # We join the users table so we know the real identity behind the comment
    comments = conn.execute('''
        SELECT c.id, c.content, c.author_id, u.username, u.role
        FROM comments c
        JOIN users u ON c.author_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.id ASC
    ''', (post_id,)).fetchall()
    conn.close()

    comment_list = []
    is_admin = current_user.get('role') == 'admin'

    for row in comments:
        comment_dict = dict(row)

        # 🛡️ THE SHIELD LOGIC 🛡️
        if is_admin:
            # Admins see the real username and ID
            comment_dict['author_display'] = f"🕵️ {row['username']} (ID: {row['author_id']})"
        elif row['role'] == 'admin':
            # Highlight admin announcements
            comment_dict['author_display'] = "🛡️ Administrator"
        else:
            # Regular students just see 'Anonymous'
            comment_dict['author_display'] = "👻 Anonymous Peer"

        # DANGER: We must delete the real data before sending it to the browser!
        del comment_dict['username']
        del comment_dict['author_id']
        del comment_dict['role']

        comment_list.append(comment_dict)

    return jsonify({"status": "success", "data": comment_list}), 200


# --- 4. REPORT A REVIEW ---
@interactions_bp.route('/comments/<int:comment_id>/report', methods=['POST'])
@token_required
def report_comment(current_user, comment_id):
    conn = get_db_connection()
    # Flip the is_reported flag to 1 (True)
    conn.execute('UPDATE comments SET is_reported = 1 WHERE id = ?', (comment_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Review reported to admins."}), 200


# --- 5. DELETE A REVIEW ---
@interactions_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_comment(current_user, comment_id):
    conn = get_db_connection()

    # SECURITY CHECK: We need to find out who owns the POST this comment is attached to
    comment_data = conn.execute('''
        SELECT c.post_id, p.author_id 
        FROM comments c 
        JOIN posts p ON c.post_id = p.id 
        WHERE c.id = ?
    ''', (comment_id,)).fetchone()

    if not comment_data:
        conn.close()
        return jsonify({"status": "error", "message": "Review not found"}), 404

    is_admin = current_user.get('role') == 'admin'
    is_post_owner = current_user.get('user_id') == comment_data['author_id']

    # If they are neither the admin nor the owner of the post, block them!
    if not (is_admin or is_post_owner):
        conn.close()
        return jsonify({"status": "error", "message": "Access denied. Only the post owner can delete reviews."}), 403

    conn.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Review permanently deleted."}), 200


# --- 6. ADMIN: GET ALL REPORTED REVIEWS ---
@interactions_bp.route('/comments/reported', methods=['GET'])
@token_required
def get_reported_comments(current_user):
    # Security: Kick out anyone who isn't an admin
    if current_user.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Access denied"}), 403

    conn = get_db_connection()
    # Fetch the reported comments AND unmask the real author's username
    reports = conn.execute('''
        SELECT c.id, c.content, c.post_id, u.username as real_author 
        FROM comments c 
        JOIN users u ON c.author_id = u.id 
        WHERE c.is_reported = 1
    ''').fetchall()
    conn.close()

    return jsonify({"status": "success", "data": [dict(r) for r in reports]}), 200


# --- 7. ADMIN: DISMISS A REPORT ---
@interactions_bp.route('/comments/<int:comment_id>/dismiss', methods=['POST'])
@token_required
def dismiss_report(current_user, comment_id):
    if current_user.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Access denied"}), 403

    conn = get_db_connection()
    # Flip the flag back to 0 (False) so it disappears from the admin dashboard
    conn.execute('UPDATE comments SET is_reported = 0 WHERE id = ?', (comment_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Report dismissed."}), 200