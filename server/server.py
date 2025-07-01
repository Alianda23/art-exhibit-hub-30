
from flask import Flask, request, jsonify
from flask_cors import CORS
from auth import (
    register_user, register_artist, login_user, login_artist, login_admin,
    validate_user_credentials
)
from middleware import token_required, admin_required, artist_required
from artwork import setup_artwork_routes
from exhibition import setup_exhibition_routes
from contact import setup_contact_routes
from db_operations import setup_db_routes
from mpesa import setup_mpesa_routes
from validate_credentials import setup_validate_credentials_routes

app = Flask(__name__)
CORS(app)

# Setup all routes
setup_artwork_routes(app)
setup_exhibition_routes(app)
setup_contact_routes(app)
setup_db_routes(app)
setup_mpesa_routes(app)
setup_validate_credentials_routes(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    result = register_user(data['name'], data['email'], data['password'], data['phone'])
    return jsonify(result)

@app.route('/register-artist', methods=['POST'])
def register_artist_route():
    data = request.get_json()
    result = register_artist(data['name'], data['email'], data['password'], data['phone'], data.get('bio', ''))
    return jsonify(result)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    result = login_user(data['email'], data['password'])
    return jsonify(result)

@app.route('/artist-login', methods=['POST'])
def artist_login():
    data = request.get_json()
    result = login_artist(data['email'], data['password'])
    return jsonify(result)

@app.route('/admin-login', methods=['POST'])
def admin_login():
    data = request.get_json()
    result = login_admin(data['email'], data['password'])
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
