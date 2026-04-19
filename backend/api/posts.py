# api/posts.py
import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from database import get_db_connection
from api.middleware import token_required

posts_bp = Blueprint('posts', __name__)

# --- UPLOAD CONFIGURATION ---
# Point this exactly to the static/uploads folder you just created
UPLOAD_FOLDER = os.path.join('static', 'uploads')
# Only allow safe file types for pictures and documents
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx'}


def allowed_file(filename):
    """Checks if the uploaded file has a safe extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- ENDPOINTS --
@posts_bp.route('', methods=['GET'])
def get_all_posts():
    """Fetch all posts, with optional search filtering"""
    # Look for a search query in the URL (e.g., ?q=science)
    search_query = request.args.get('q', '')

    # NEW: Get the page number from the URL (default to page 1)
    page = int(request.args.get('page', 1))
    limit = 5  # We will load 5 posts at a time so it is easy to test!
    offset = (page - 1) * limit

    conn = get_db_connection()

    if search_query:
        # The % symbols act as wildcards, finding the word anywhere in the content
        posts = conn.execute(
            'SELECT * FROM posts WHERE content LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?',
            (f'%{search_query}%', limit, offset)
        ).fetchall()
    else:
        # If no search query, just get everything
        posts = conn.execute('SELECT * FROM posts ORDER BY id DESC LIMIT ? OFFSET ?',(limit,offset)).fetchall()

    conn.close()


    return jsonify({
        "status": "success",
        "data": [dict(post) for post in posts],
        "page": page,
        "limit": limit
    }), 200

# backend/api/posts.py

@posts_bp.route('', methods=['POST'])
@token_required
def create_post(current_user):
    # Use request.form instead of request.get_json() for FormData
    content = request.form.get('content')
    post_type = request.form.get('post_type', 'blog')
    author_id = current_user['user_id']
    file_url = None

    # Handle optional file upload
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            # Clean the filename to prevent hacking (secure_filename)
            filename = secure_filename(file.filename)
            # Create a unique name so users don't overwrite each other's files
            unique_name = f"user_{author_id}_{filename}"

            upload_path = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)

            file.save(os.path.join(upload_path, unique_name))
            file_url = f"/uploads/{unique_name}"

    if not content:
        return jsonify({"status": "error", "message": "Content is required"}), 400

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO posts (author_id, content, post_type,file_path) VALUES (?, ?, ?, ?)',
        (author_id, content, post_type,file_url)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Post created!"}), 201

# ... your existing get_all_posts and create_post routes ...

@posts_bp.route('/me', methods=['GET'])
@token_required
def get_my_posts(current_user):
    """Fetch posts created only by the logged-in user"""
    user_id = current_user['user_id']

    conn = get_db_connection()
    # Notice the WHERE clause filtering by author_id!
    posts = conn.execute('SELECT * FROM posts WHERE author_id = ? ORDER BY id DESC', (user_id,)).fetchall()
    conn.close()

    post_list = [dict(post) for post in posts]

    return jsonify({
        "status": "success",
        "data": post_list
    }), 200


@posts_bp.route('/<int:post_id>', methods=['DELETE'])
@token_required
def delete_post(current_user, post_id):
    """Allows admins AND the post author to delete a specific post"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # First, find the post to see who owns it
    post = cursor.execute('SELECT author_id FROM posts WHERE id = ?', (post_id,)).fetchone()

    if not post:
        conn.close()
        return jsonify({"status": "error", "message": "Post not found."}), 404

    # SECURITY CHECK: Are they an Admin OR the Author?
    is_admin = current_user.get('role') == 'admin'
    is_author = current_user.get('user_id') == post['author_id']

    if not (is_admin or is_author):
        conn.close()
        return jsonify({"status": "error", "message": "Access denied. You can only delete your own posts."}), 403

    # If they pass the check, execute the deletion
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    cursor.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))  # Clean up comments too

    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Post permanently deleted."}), 200