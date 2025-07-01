
from flask import request, jsonify
from auth import validate_user_credentials

def setup_validate_credentials_routes(app):
    @app.route('/validate-credentials', methods=['POST'])
    def validate_credentials():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'valid': False, 'error': 'No JSON data provided'}), 400
            
            email = data.get('email')
            password = data.get('password')
            user_type = data.get('userType')
            
            if not email or not password or not user_type:
                return jsonify({'valid': False, 'error': 'Email, password, and userType are required'}), 400
            
            # Validate credentials using the existing function
            result = validate_user_credentials(email, password, user_type)
            
            if result.get('valid'):
                return jsonify({'valid': True}), 200
            else:
                return jsonify({'valid': False, 'error': result.get('error', 'Invalid credentials')}), 200
        
        except Exception as e:
            print(f"Error in validate_credentials: {e}")
            return jsonify({'valid': False, 'error': 'Server error'}), 500
