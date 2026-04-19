# app.py
import os
from flask import send_from_directory
from flask import Flask, jsonify
from api.auth import auth_bp
from api.posts import posts_bp
from api.interactions import interactions_bp
from api.moderation import moderation_bp
from config import Config
from database import get_db_connection

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def create_app():
    # 1. Create the app ONCE
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config.from_object(Config)
    # In backend/app.py
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

    # 2. Attach the CORS Sledgehammer to it
    @app.after_request
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        return response

    # 3. Register your blueprints
    app.register_blueprint(posts_bp, url_prefix='/api/posts')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(interactions_bp, url_prefix='/api/interactions')
    app.register_blueprint(moderation_bp, url_prefix='/api/moderation')

    # 4. Test the database connection
    with app.app_context():
        conn = get_db_connection()
        if conn:
            conn.close()

    # Route to actually view the uploaded files in the browser
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # 5. Health Check Route
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "ok",
            "message": "PeerView backend is active!"
        })

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)