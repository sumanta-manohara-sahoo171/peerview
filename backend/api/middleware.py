# api/middleware.py
import jwt
from functools import wraps
from flask import request, jsonify
from config import Config


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # The frontend will send the token in the headers like this: "Bearer eyJhb..."
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split(" ")
            if len(parts) == 2 and parts[0] == "Bearer":
                token = parts[1]

        if not token:
            return jsonify({"status": "error", "message": "Token is missing! Please log in."}), 401

        try:
            # Decode the token using the secret key we set up in config.py
            current_user = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"status": "error", "message": "Token has expired! Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"status": "error", "message": "Invalid token!"}), 401

        # If the token is valid, proceed to the route and pass the user data along!
        return f(current_user, *args, **kwargs)

    return decorated


# api/middleware.py

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        # The current_user dictionary comes from the token_required decorator
        if current_user.get('role') != 'admin':
            return jsonify({
                "status": "error",
                "message": "Access denied. Admin privileges required."
            }), 403

        return f(current_user, *args, **kwargs)

    return decorated