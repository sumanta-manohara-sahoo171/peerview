from flask import Blueprint, request, jsonify
from database import get_db_connection
from api.middleware import token_required
from api.auth import send_email

interactions_bp = Blueprint('interactions', __name__)


# --- 1. POST A REVIEW (WITH ANONYMOUS EMAIL NOTIFICATION) ---
@interactions_bp.route('/comments', methods=['POST'])
@token_required
def post_comment(current_user):
    data = request.get_json()
    post_id = data.get('post_id')
    content = data.get('content')

    if not post_id or not content:
        return jsonify({"status": "error", "message": "Post ID and content required"}), 400

    conn = get_db_connection()
    try:
        # Save comment
        conn.execute(
            'INSERT INTO comments (post_id, author_id, content) VALUES (?, ?, ?)',
            (post_id, current_user['user_id'], content)
        )

        # Get author info to send them an email
        author_info = conn.execute('''
            SELECT u.email, u.username, p.content as post_text
            FROM posts p
            JOIN users u ON p.author_id = u.id 
            WHERE p.id = ?
        ''', (post_id,)).fetchone()

        conn.commit()

        # Send Notification Email
        if author_info and author_info['email']:
            # Optional: Don't notify if user is commenting on their own post
            if author_info['email'] != current_user.get('email'):
                subject = "New Review on your PeerView Post!"
                body = f"Hello {author_info['username']},\n\n" \
                       f"A peer just left an anonymous review on your post!\n\n" \
                       f"Post excerpt: \"{author_info['post_text'][:50]}...\"\n" \
                       f"Review: \"{content}\"\n\n" \
                       f"Log in to PeerView to see the full feedback."
                send_email(author_info['email'], subject, body)

        return jsonify({"status": "success", "message": "Review posted anonymously"}), 201
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": "Server error"}), 500
    finally:
        conn.close()


# --- 2. GET COMMENTS FOR A POST (ANONYMOUS FEED) ---
@interactions_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
@token_required
def get_comments(current_user, post_id):
    conn = get_db_connection()
    # We fetch the data but hide real usernames from the browser
    comments = conn.execute('''
        SELECT c.*, u.username as real_name 
        FROM comments c 
        JOIN users u ON c.author_id = u.id 
        WHERE c.post_id = ? 
        ORDER BY c.created_at ASC
    ''', (post_id,)).fetchall()
    conn.close()

    result = []
    for c in comments:
        comment_dict = dict(c)

        # Logic: If I wrote it, show "You", otherwise show "Anonymous Peer"
        if c['author_id'] == current_user['user_id']:
            comment_dict['author_display'] = "You (Anonymous)"
            comment_dict['is_mine'] = True
        else:
            comment_dict['author_display'] = "Anonymous Peer"
            comment_dict['is_mine'] = False

        # Security: Delete the real name before sending to the frontend
        if 'real_name' in comment_dict:
            del comment_dict['real_name']

        result.append(comment_dict)

    return jsonify({"status": "success", "data": result}), 200


# --- 3. VOTING SYSTEM ---
@interactions_bp.route('/votes', methods=['POST'])
@token_required
def cast_vote(current_user):
    data = request.get_json()
    post_id = data.get('post_id')
    vote_type = data.get('vote_type')
    conn = get_db_connection()

    existing = conn.execute('SELECT vote_type FROM votes WHERE post_id=? AND user_id=?',
                            (post_id, current_user['user_id'])).fetchone()
    if existing:
        if existing['vote_type'] == vote_type:
            conn.execute('DELETE FROM votes WHERE post_id=? AND user_id=?', (post_id, current_user['user_id']))
        else:
            conn.execute('UPDATE votes SET vote_type=? WHERE post_id=? AND user_id=?',
                         (vote_type, post_id, current_user['user_id']))
    else:
        conn.execute('INSERT INTO votes (post_id, user_id, vote_type) VALUES (?, ?, ?)',
                     (post_id, current_user['user_id'], vote_type))

    up = conn.execute('SELECT COUNT(*) FROM votes WHERE post_id=? AND vote_type=1', (post_id,)).fetchone()[0]
    down = conn.execute('SELECT COUNT(*) FROM votes WHERE post_id=? AND vote_type=-1', (post_id,)).fetchone()[0]
    conn.execute('UPDATE posts SET upvotes=?, downvotes=? WHERE id=?', (up, down, post_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 200


# --- 4. REPORT A REVIEW ---
@interactions_bp.route('/comments/<int:comment_id>/report', methods=['POST'])
@token_required
def report_comment(current_user, comment_id):
    conn = get_db_connection()
    conn.execute('UPDATE comments SET is_reported = 1 WHERE id = ?', (comment_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Review reported for moderation."}), 200


# --- 5. ADMIN: VIEW REPORTED REVIEWS (REVEALS IDENTITY) ---
@interactions_bp.route('/comments/reported', methods=['GET'])
@token_required
def get_reported_comments(current_user):
    if current_user['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    conn = get_db_connection()
    reported = conn.execute('''
        SELECT c.*, u.email as real_author 
        FROM comments c 
        JOIN users u ON c.author_id = u.id 
        WHERE c.is_reported = 1
    ''', ).fetchall()
    conn.close()
    return jsonify({"status": "success", "data": [dict(r) for r in reported]}), 200


# --- 6. ADMIN: DISMISS REPORT ---
@interactions_bp.route('/comments/<int:comment_id>/dismiss', methods=['POST'])
@token_required
def dismiss_report(current_user, comment_id):
    if current_user['role'] != 'admin': return jsonify({"status": "error"}), 403
    conn = get_db_connection()
    conn.execute('UPDATE comments SET is_reported = 0 WHERE id = ?', (comment_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 200


# --- 7. DELETE A REVIEW ---
@interactions_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_comment(current_user, comment_id):
    conn = get_db_connection()
    comment = conn.execute('SELECT * FROM comments WHERE id = ?', (comment_id,)).fetchone()
    if not comment:
        conn.close()
        return jsonify({"status": "error", "message": "Not found"}), 404

    # Permission: Admin can delete anything, users can delete their own
    if current_user['role'] == 'admin' or current_user['user_id'] == comment['author_id']:
        conn.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Deleted"}), 200

    conn.close()
    return jsonify({"status": "error", "message": "Unauthorized"}), 403