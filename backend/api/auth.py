import jwt
import datetime
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection
from api.middleware import token_required
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

auth_bp = Blueprint('auth', __name__)


def generate_otp():
    return str(random.randint(100000, 999999))


def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("Failed to send email:", e)
        return False


# --- 1. REGISTRATION (UPGRADED WITH VERIFICATION) ---
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"status": "error", "message": "Username, email, and password are required"}), 400

    hashed_password = generate_password_hash(password)
    otp = generate_otp()
    expiry = (datetime.datetime.utcnow() + datetime.timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    try:
        # Save user as unverified (is_verified = 0) with their OTP
        conn.execute(
            'INSERT INTO users (username, email, password_hash, otp_code, otp_expiry, is_verified) VALUES (?, ?, ?, ?, ?, 0)',
            (username, email, hashed_password, otp, expiry)
        )
        conn.commit()

        # Send the welcome verification email
        body = f"Welcome to PeerView, {username}!\n\nYour account verification code is: {otp}\n\nThis code will expire in 15 minutes."
        send_email(email, "Verify Your PeerView Account", body)

        return jsonify({"status": "success",
                        "message": "Registration successful! Please check your email for the verification code."}), 201
    except conn.IntegrityError as e:
        error_msg = str(e).lower()
        if "email" in error_msg:
            return jsonify({"status": "error", "message": "This email is already registered."}), 409
        else:
            return jsonify({"status": "error", "message": "Username is already taken."}), 409
    finally:
        conn.close()


# --- 1.5 NEW: VERIFY EMAIL ROUTE ---
@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if not user or user['otp_code'] != otp:
        conn.close()
        return jsonify({"status": "error", "message": "Invalid verification code."}), 400

    expiry_time = datetime.datetime.strptime(user['otp_expiry'], '%Y-%m-%d %H:%M:%S')
    if datetime.datetime.utcnow() > expiry_time:
        conn.close()
        return jsonify(
            {"status": "error", "message": "Code has expired. Please register again or request a new code."}), 400

    # Mark user as verified
    conn.execute('UPDATE users SET is_verified = 1, otp_code = NULL, otp_expiry = NULL WHERE email = ?', (email,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Email verified successfully! You can now log in."}), 200


# --- 2. LOGIN (UPGRADED) ---
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        # NEW: Block login if not verified
        if not user['is_verified']:
            return jsonify({"status": "error", "message": "Please verify your email before logging in!"}), 403

        token = jwt.encode({
            'user_id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")

        return jsonify({"status": "success", "token": token}), 200

    return jsonify({"status": "error", "message": "Invalid email or password"}), 401


# --- 3. FORGOT PASSWORD ---
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.get_json().get('email')
    conn = get_db_connection()
    user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()

    if not user:
        conn.close()
        return jsonify({"status": "success", "message": "If that email exists, an OTP was sent."}), 200

    otp = generate_otp()
    expiry = (datetime.datetime.utcnow() + datetime.timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')

    conn.execute('UPDATE users SET otp_code = ?, otp_expiry = ? WHERE email = ?', (otp, expiry, email))
    conn.commit()
    conn.close()

    body = f"Hello from PeerView!\n\nYour Password Reset OTP is: {otp}\n\nThis code will expire in 10 minutes."
    send_email(email, "PeerView - Password Reset OTP", body)
    return jsonify({"status": "success", "message": "OTP sent successfully."}), 200


# --- 4. RESET PASSWORD ---
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    new_password = data.get('new_password')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if not user or user['otp_code'] != otp:
        conn.close()
        return jsonify({"status": "error", "message": "Invalid OTP code."}), 400

    expiry_time = datetime.datetime.strptime(user['otp_expiry'], '%Y-%m-%d %H:%M:%S')
    if datetime.datetime.utcnow() > expiry_time:
        conn.close()
        return jsonify({"status": "error", "message": "OTP has expired. Please request a new one."}), 400

    hashed_password = generate_password_hash(new_password)
    conn.execute('UPDATE users SET password_hash = ?, otp_code = NULL, otp_expiry = NULL WHERE email = ?',
                 (hashed_password, email))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Password reset successfully! You can now log in."}), 200


# --- 5. PROFILE MANAGEMENT ---
@auth_bp.route('/profile', methods=['GET', 'PUT'])
@token_required
def profile(current_user):
    conn = get_db_connection()
    if request.method == 'GET':
        user = conn.execute('SELECT id, username, email, role, bio, avatar_url FROM users WHERE id = ?',
                            (current_user['user_id'],)).fetchone()
        conn.close()
        if user:
            return jsonify({"status": "success", "data": dict(user)}), 200
        return jsonify({"status": "error", "message": "User not found"}), 404

    if request.method == 'PUT':
        bio = request.form.get('bio')
        avatar = request.files.get('avatar')
        update_query = 'UPDATE users SET bio = ?'
        params = [bio]

        if avatar:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_folder = os.path.join(base_dir, 'uploads')
            os.makedirs(upload_folder, exist_ok=True)

            filename = f"avatar_{current_user['user_id']}_{avatar.filename}"
            file_path = os.path.join(upload_folder, filename)
            avatar.save(file_path)

            update_query += ', avatar_url = ?'
            params.append(f'/uploads/{filename}')

        update_query += ' WHERE id = ?'
        params.append(current_user['user_id'])
        conn.execute(update_query, tuple(params))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Profile updated"}), 200