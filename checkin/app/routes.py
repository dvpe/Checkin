from flask import Blueprint, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return jsonify({"message": "Welcome to Flask API!"})

@main_bp.route('/health')
def health():
    return jsonify({"status": "healthy"}) 