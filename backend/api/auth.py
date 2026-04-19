import jwt
import datetime
import sqlite3
import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import get_db_connection
from config import Config
from api.middleware import token_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register_user():  # <-- Updated function name here!
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password required"}), 400

    # Default all new sign-ups to 'student'
    role = data.get('role', 'student')

    # Hash the password for security
    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        # Explicitly name the 3 columns, provide 3 placeholders (?), and 3 variables.
        conn.execute(
            'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
            (username, hashed_password, role)
        )
        conn.commit()
        conn.close()

        return jsonify({"status": "success", "message": "User created successfully!"}), 201

    except sqlite3.IntegrityError:
        # This catches if someone tries to register a username that is already taken
        return jsonify({"status": "error", "message": "Username already exists."}), 409
    except Exception as e:
        print(f"DEBUG REGISTER ERROR: {e}")
        return jsonify({"status": "error", "message": "Server error during registration."}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Verifies credentials and hands out a JWT token"""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required"}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if not user:
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401

        # Check if account is active
    if user['status'] != 'active':
        return jsonify({"status": "error", "message": "This account is currently deactivated."}), 403

    if check_password_hash(user['password'], password):
        # PYTHON 3.14 FIX: Use timezone-aware UTC
        now = datetime.datetime.now(datetime.timezone.utc)
        token_payload = {
            "user_id": user['id'],
            "role": user['role'],
            "exp": now + datetime.timedelta(hours=24)
        }

        token = jwt.encode(token_payload, Config.SECRET_KEY, algorithm="HS256")

        return jsonify({
            "status": "success",
            "message": "Welcome back!",
            "token": token
        }), 200

    return jsonify({"status": "error", "message": "Invalid username or password"}), 401

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Fetches the logged-in user's profile data"""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT username, role, bio, avatar_url FROM users WHERE id = ?',
        (current_user['user_id'],)
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    return jsonify({
        "status": "success",
        "data": dict(user)
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Updates the user's bio and avatar"""
    bio = request.form.get('bio')
    avatar_url = None

    # 1. Handle Avatar Upload (if they attached a new picture)
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file.filename != '':
            filename = secure_filename(file.filename)
            unique_name = f"avatar_{current_user['user_id']}_{filename}"

            upload_path = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_path):
                os.makedirs(upload_path, exist_ok=True)

            file.save(os.path.join(upload_path, unique_name))
            avatar_url = f"/static/uploads/{unique_name}"

    # 2. Update the Database
    conn = get_db_connection()
    if avatar_url:
        # Update both bio AND picture
        conn.execute('UPDATE users SET bio = ?, avatar_url = ? WHERE id = ?',
                     (bio, avatar_url, current_user['user_id']))
    else:
        # Just update the bio
        conn.execute('UPDATE users SET bio = ? WHERE id = ?', (bio, current_user['user_id']))

    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Profile updated!"}), 200