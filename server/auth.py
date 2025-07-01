
import hashlib
import secrets
from database import get_db_connection, json_dumps
import jwt
import datetime
import os
from decimal import Decimal
from middleware import SECRET_KEY  # Import the shared SECRET_KEY

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_user_credentials(email, password, user_type):
    """Validate user credentials without logging in"""
    connection = get_db_connection()
    if connection is None:
        return {"valid": False, "error": "Database connection failed"}
    
    cursor = connection.cursor()
    hashed_password = hash_password(password)
    
    try:
        if user_type == 'user':
            query = "SELECT id, name FROM users WHERE email = %s AND password = %s"
        elif user_type == 'artist':
            query = "SELECT id, name FROM artists WHERE email = %s AND password = %s"
        elif user_type == 'admin':
            query = "SELECT id, name FROM admins WHERE email = %s AND password = %s"
        else:
            return {"valid": False, "error": "Invalid user type"}
        
        cursor.execute(query, (email, hashed_password))
        user = cursor.fetchone()
        
        if user:
            return {"valid": True}
        else:
            return {"valid": False, "error": "Invalid credentials"}
    
    except Exception as e:
        print(f"Error validating credentials: {e}")
        return {"valid": False, "error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def register_user(name, email, password, phone):
    """Register a new user"""
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    hashed_password = hash_password(password)
    
    try:
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return {"error": "Email already registered"}
        
        # Insert the new user
        query = """
        INSERT INTO users (name, email, password, phone)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (name, email, hashed_password, phone))
        connection.commit()
        
        # Get the new user ID
        user_id = cursor.lastrowid
        
        # Generate token for the new user
        token = generate_token(user_id, name, False)
        
        return {
            "token": token,
            "user_id": user_id,
            "name": name
        }
    except Exception as e:
        print(f"Error registering user: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def register_artist(name, email, password, phone, bio=""):
    """Register a new artist"""
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    hashed_password = hash_password(password)
    
    try:
        # Check if email already exists
        cursor.execute("SELECT id FROM artists WHERE email = %s", (email,))
        if cursor.fetchone():
            return {"error": "Email already registered"}
        
        # Insert the new artist
        query = """
        INSERT INTO artists (name, email, password, phone, bio)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, email, hashed_password, phone, bio))
        connection.commit()
        
        # Get the new artist ID
        artist_id = cursor.lastrowid
        
        # Generate token for the new artist
        token = generate_token(artist_id, name, False, True)
        
        return {
            "token": token,
            "artist_id": artist_id,
            "name": name
        }
    except Exception as e:
        print(f"Error registering artist: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def login_user(email, password):
    """Login a user"""
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    hashed_password = hash_password(password)
    
    try:
        # Check user credentials
        query = "SELECT id, name FROM users WHERE email = %s AND password = %s"
        cursor.execute(query, (email, hashed_password))
        user = cursor.fetchone()
        
        if not user:
            return {"error": "Invalid credentials"}
        
        # Generate token for the user
        user_id, name = user
        token = generate_token(user_id, name, False)
        
        return {
            "token": token,
            "user_id": user_id,
            "name": name
        }
    except Exception as e:
        print(f"Error logging in user: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def login_artist(email, password):
    """Login an artist"""
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    hashed_password = hash_password(password)
    
    try:
        # Check artist credentials
        query = "SELECT id, name FROM artists WHERE email = %s AND password = %s"
        cursor.execute(query, (email, hashed_password))
        artist = cursor.fetchone()
        
        if not artist:
            return {"error": "Invalid credentials"}
        
        # Generate token for the artist
        artist_id, name = artist
        token = generate_token(artist_id, name, False, True)
        
        return {
            "token": token,
            "artist_id": artist_id,
            "name": name
        }
    except Exception as e:
        print(f"Error logging in artist: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def login_admin(email, password):
    """Login an admin"""
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    hashed_password = hash_password(password)
    
    try:
        # Check admin credentials
        query = "SELECT id, name FROM admins WHERE email = %s AND password = %s"
        cursor.execute(query, (email, hashed_password))
        admin = cursor.fetchone()
        
        if not admin:
            return {"error": "Invalid admin credentials"}
        
        # Generate token for the admin
        admin_id, name = admin
        token = generate_token(admin_id, name, True)
        
        print(f"Admin login successful: {name}, admin_id: {admin_id}, token: {token[:20]}...")
        
        return {
            "token": token,
            "admin_id": admin_id,
            "name": name
        }
    except Exception as e:
        print(f"Error logging in admin: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def generate_token(user_id, name, is_admin, is_artist=False):
    """Generate a JWT token for authentication"""
    payload = {
        "sub": str(user_id),  # Ensure user_id is converted to string
        "name": name,
        "is_admin": is_admin,
        "is_artist": is_artist,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    
    print(f"Generating token with payload: {payload}")
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def verify_token(token):
    """Verify a JWT token"""
    try:
        print(f"Verifying token: {token[:20]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print(f"Token decoded successfully: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        print("Token verification failed: Token expired")
        return {"error": "Token expired"}
    except jwt.InvalidTokenError as e:
        print(f"Token verification failed: Invalid token - {str(e)}")
        return {"error": f"Invalid token: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error during token verification: {str(e)}")
        return {"error": f"Token verification error: {str(e)}"}

def create_admin(name, email, password):
    """Create a new admin (called from terminal/script)"""
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    hashed_password = hash_password(password)
    
    try:
        # Check if email already exists
        cursor.execute("SELECT id FROM admins WHERE email = %s", (email,))
        if cursor.fetchone():
            return {"error": "Admin email already exists"}
        
        # Insert the new admin
        query = """
        INSERT INTO admins (name, email, password)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (name, email, hashed_password))
        connection.commit()
        
        return {
            "success": True,
            "admin_id": cursor.lastrowid,
            "name": name
        }
    except Exception as e:
        print(f"Error creating admin: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
