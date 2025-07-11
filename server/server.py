import os
import json
import http.server
import socketserver
import urllib.parse
import mimetypes
from http import HTTPStatus
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from decimal import Decimal

# Import modules
from auth import register_user, login_user, login_admin, register_artist, login_artist
from artwork import get_all_artworks, get_artwork, create_artwork, update_artwork, delete_artwork
from exhibition import get_all_exhibitions, get_exhibition, create_exhibition, update_exhibition, delete_exhibition
from contact import create_contact_message, get_messages, update_message, json_dumps
from db_setup import initialize_database
from middleware import auth_required, admin_required, extract_auth_token, verify_token
from mpesa import handle_stk_push_request, check_transaction_status, handle_mpesa_callback
from db_operations import get_all_tickets, get_all_orders, get_artist_artworks, get_artist_orders, get_all_artists, get_user_orders
from database import get_db_connection  # Add this import

# Define the port
PORT = 8000

# Ensure the static/uploads directory exists
def ensure_uploads_directory():
    uploads_dir = os.path.join(os.path.dirname(__file__), "static", "uploads")
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        print(f"Created directory: {uploads_dir}")

# Call this function to ensure directory exists
ensure_uploads_directory()

# Create a default placeholder.svg if it doesn't exist
def create_placeholder_svg():
    placeholder_path = os.path.join(os.path.dirname(__file__), "static", "placeholder.svg")
    if not os.path.exists(placeholder_path):
        try:
            # Create a simple SVG placeholder
            svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#f3f4f6"/>
  <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="18" fill="#9ca3af" text-anchor="middle" dy=".3em">
    Image Not Available
  </text>
</svg>'''
            with open(placeholder_path, "w") as f:
                f.write(svg_content)
            print(f"Created placeholder.svg at: {placeholder_path}")
        except Exception as e:
            print(f"Failed to create placeholder.svg: {e}")

# Create a default exhibition image if it doesn't exist
def create_default_exhibition_image():
    default_image_path = os.path.join(os.path.dirname(__file__), "static", "uploads", "default_exhibition.jpg")
    if not os.path.exists(default_image_path):
        try:
            # Create a simple colored rectangle as the default image
            # This would be better with PIL, but let's use a placeholder approach
            from shutil import copyfile
            
            # Copy a placeholder from public if it exists
            source_placeholder = os.path.join(os.path.dirname(__file__), "..", "public", "placeholder.svg")
            if os.path.exists(source_placeholder):
                copyfile(source_placeholder, default_image_path)
                print(f"Created default exhibition image from placeholder")
            else:
                # Create an empty file as fallback
                with open(default_image_path, "w") as f:
                    f.write("Default Exhibition Image Placeholder")
                print(f"Created empty default exhibition image")
        except Exception as e:
            print(f"Failed to create default exhibition image: {e}")

# Call these functions to ensure the files exist
create_placeholder_svg()
create_default_exhibition_image()

# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)

# Mock data for tickets (in a real app, this would come from a database)
# We'll use this for demo purposes
mock_tickets = [
    {
        "id": "ticket-001",
        "userId": "user-123",
        "userName": "John Doe",
        "exhibitionId": "exhibition-1",
        "exhibitionTitle": "Modern Art Showcase",
        "bookingDate": "2025-04-20T14:00:00",
        "ticketCode": "EXHB-001-123",
        "slots": 2,
        "status": "active"
    },
    {
        "id": "ticket-002",
        "userId": "user-456",
        "userName": "Jane Smith",
        "exhibitionId": "exhibition-2",
        "exhibitionTitle": "Classical Paintings",
        "bookingDate": "2025-04-21T10:30:00",
        "ticketCode": "EXHB-002-456",
        "slots": 1,
        "status": "used"
    },
    {
        "id": "ticket-003",
        "userId": "user-789",
        "userName": "Alex Johnson",
        "exhibitionId": "exhibition-1",
        "exhibitionTitle": "Modern Art Showcase",
        "bookingDate": "2025-04-22T16:15:00",
        "ticketCode": "EXHB-001-789",
        "slots": 3,
        "status": "cancelled"
    }
]

# Function to get all tickets (mock implementation)
def get_all_tickets(auth_header):
    """Get all tickets (admin only)"""
    print(f"Getting all tickets with auth header: {auth_header[:20]}... (truncated)")
    
    # Extract and verify token - directly use the token from auth_header
    token = extract_auth_token(auth_header)
    if not token:
        print("Authentication required - no token found")
        return {"error": "Authentication required"}
    
    payload = verify_token(token)
    if isinstance(payload, dict) and "error" in payload:
        print(f"Authentication failed: {payload['error']}")
        return {"error": payload["error"]}
    
    # Check if user is admin
    if not payload.get("is_admin", False):
        print("Access denied - not an admin user")
        return {"error": "Unauthorized access: Admin privileges required"}
    
    print(f"Admin user authenticated, returning {len(mock_tickets)} tickets")
    # Return tickets data
    return {"tickets": mock_tickets}

# Function to generate exhibition ticket (mock implementation)
def generate_ticket(booking_id, auth_header):
    # Extract and verify token
    token = extract_auth_token(auth_header)
    if not token:
        return {"error": "Authentication required"}
    
    payload = verify_token(token)
    if isinstance(payload, dict) and "error" in payload:
        return {"error": payload["error"]}
    
    # In a real application, we would generate a PDF here
    # For demo purposes, we'll return mock data
    return {
        "pdfData": "Mock PDF data for ticket " + booking_id,
        "success": True
    }

class RequestHandler(http.server.BaseHTTPRequestHandler):
    
    def _set_response(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_response()
    
    def serve_static_file(self, file_path):
        """Serve a static file based on its MIME type"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                # If requesting placeholder.svg specifically, serve it from static directory
                if file_path.endswith('placeholder.svg'):
                    placeholder_path = os.path.join(os.path.dirname(__file__), "static", "placeholder.svg")
                    if os.path.exists(placeholder_path):
                        file_path = placeholder_path
                    else:
                        self.send_response(404)
                        self.end_headers()
                        return
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
                
            # Determine the content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
                
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Set headers
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-Length', str(file_size))
            self.end_headers()
            
            # Read and send the file
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
                
        except Exception as e:
            print(f"Error serving static file: {e}")
            self.send_response(500)
            self.end_headers()
    
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # Handle static files (images, CSS, JS, etc.)
        if path.startswith('/static/'):
            file_path = os.path.join(os.path.dirname(__file__), path[1:])
            # Debugging info
            print(f"Serving static file: {file_path}")
            self.serve_static_file(file_path)
            return
        
        # Handle placeholder.svg specifically
        elif path == '/placeholder.svg':
            file_path = os.path.join(os.path.dirname(__file__), "static", "placeholder.svg")
            print(f"Serving placeholder.svg from: {file_path}")
            self.serve_static_file(file_path)
            return
        
        # Handle API endpoints
        # Handle GET /artworks
        if path == '/artworks':
            response = get_all_artworks()
            self._set_response()
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Handle GET /artworks/{id}
        elif path.startswith('/artworks/') and len(path.split('/')) == 3:
            artwork_id = path.split('/')[2]
            response = get_artwork(artwork_id)
            self._set_response()
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Handle GET /exhibitions
        elif path == '/exhibitions':
            response = get_all_exhibitions()
            self._set_response()
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Handle GET /exhibitions/{id}
        elif path.startswith('/exhibitions/') and len(path.split('/')) == 3:
            exhibition_id = path.split('/')[2]
            response = get_exhibition(exhibition_id)
            self._set_response()
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Handle GET /user/{user_id}/orders - NEW ENDPOINT
        elif path.startswith('/user/') and path.endswith('/orders') and len(path.split('/')) == 4:
            user_id = path.split('/')[2]
            print(f"Processing GET /user/{user_id}/orders request")
            
            # Verify authentication
            auth_header = self.headers.get('Authorization', '')
            token = extract_auth_token(auth_header)
            if not token:
                print("Authentication required - no token found")
                self._set_response(401)
                self.wfile.write(json_dumps({"error": "Authentication required"}).encode())
                return
            
            payload = verify_token(token)
            if isinstance(payload, dict) and "error" in payload:
                print(f"Authentication failed: {payload['error']}")
                self._set_response(401)
                self.wfile.write(json_dumps({"error": payload["error"]}).encode())
                return
            
            # Check if user is requesting their own data or is admin
            requesting_user_id = str(payload.get("sub"))
            is_admin = payload.get("is_admin", False)
            
            if not is_admin and requesting_user_id != user_id:
                print(f"Access denied - user {requesting_user_id} trying to access data for user {user_id}")
                self._set_response(403)
                self.wfile.write(json_dumps({"error": "Access denied - you can only view your own orders"}).encode())
                return
            
            print(f"Authorized request for user {user_id} orders")
            
            # Get user orders and bookings
            response = get_user_orders(user_id)
            print(f"User orders response: {response}")
            
            if "error" in response:
                self._set_response(500)
                self.wfile.write(json_dumps(response).encode())
                return
            
            self._set_response()
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Handle GET /messages (admin only)
        elif path == '/messages':
            print("Processing GET /messages request")
            auth_header = self.headers.get('Authorization', '')
            print(f"Authorization header: {auth_header[:20]}... (truncated)")
            
            # Get messages
            response = get_messages(auth_header)
            print(f"Get messages response: {response}")
            
            if "error" in response:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": response["error"]}).encode())
                return
            
            self._set_response()
            self.wfile.write(json_dumps(response).encode())
            return
            
        # Handle GET /tickets (admin only)
        elif path == '/tickets':
            print("Processing GET /tickets request")
            auth_header = self.headers.get('Authorization', '')
            
            # Verify admin access
            token = extract_auth_token(auth_header)
            if not token:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": "Authentication required"}).encode())
                return
            
            payload = verify_token(token)
            if not payload.get("is_admin", False):
                self._set_response(403)
                self.wfile.write(json_dumps({"error": "Admin access required"}).encode())
                return
            
            # Get tickets from database
            from db_operations import get_all_tickets
            response = get_all_tickets()
            self._set_response()
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Handle GET /orders (admin only)
        elif path == '/orders':
            print("Processing GET /orders request")
            auth_header = self.headers.get('Authorization', '')
            
            # Verify admin access
            token = extract_auth_token(auth_header)
            if not token:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": "Authentication required"}).encode())
                return
            
            payload = verify_token(token)
            if not payload.get("is_admin", False):
                self._set_response(403)
                self.wfile.write(json_dumps({"error": "Admin access required"}).encode())
                return
            
            # Get orders from database
            from db_operations import get_all_orders
            response = get_all_orders()
            self._set_response()
            self.wfile.write(json_dumps(response).encode())
            return

        # Handle GET /artists (admin only)
        elif path == '/artists':
            print("Processing GET /artists request")
            auth_header = self.headers.get('Authorization', '')
            
            # Verify admin access
            token = extract_auth_token(auth_header)
            if not token:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": "Authentication required"}).encode())
                return
            
            payload = verify_token(token)
            if not payload.get("is_admin", False):
                self._set_response(403)
                self.wfile.write(json_dumps({"error": "Admin access required"}).encode())
                return
            
            # Get artists from database
            response = get_all_artists()
            self._set_response()
            self.wfile.write(json_dumps(response).encode())
            return
            
        # Handle GET /artist/artworks (artist only)
        elif path == '/artist/artworks':
            auth_header = self.headers.get('Authorization', '')
            
            # Verify artist access
            token = extract_auth_token(auth_header)
            if not token:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": "Authentication required"}).encode())
                return
            
            payload = verify_token(token)
            if not payload.get("is_artist", False):
                self._set_response(403)
                self.wfile.write(json_dumps({"error": "Artist access required"}).encode())
                return
            
            # Get artworks by artist ID
            artist_id = payload.get("sub")
            response = get_artist_artworks(artist_id)
            self._set_response()
            self.wfile.write(json_dumps(response).encode())
            return
            
        # Handle GET /artist/orders (artist only)
        elif path == '/artist/orders':
            auth_header = self.headers.get('Authorization', '')
            
            # Verify artist access
            token = extract_auth_token(auth_header)
            if not token:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": "Authentication required"}).encode())
                return
            
            payload = verify_token(token)
            if not payload.get("is_artist", False):
                self._set_response(403)
                self.wfile.write(json_dumps({"error": "Artist access required"}).encode())
                return
            
            # Get orders for artworks by artist ID
            artist_id = payload.get("sub")
            response = get_artist_orders(artist_id)
            self._set_response()
            self.wfile.write(json_dumps(response).encode())
            return
            
        # Handle GET /tickets/generate/{id} (generate ticket)
        elif path.startswith('/tickets/generate/') and len(path.split('/')) == 4:
            booking_id = path.split('/')[3]
            print(f"Processing generate ticket request for booking {booking_id}")
            auth_header = self.headers.get('Authorization', '')
            
            # Generate ticket
            response = generate_ticket(booking_id, auth_header)
            
            if "error" in response:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": response["error"]}).encode())
                return
            
            self._set_response()
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Default 404 response
        self._set_response(404)
        self.wfile.write(json_dumps({"error": "Resource not found"}).encode())
    
    def do_POST(self):
        # Get content length
        content_length = int(self.headers.get('Content-Length', 0))
        
        # Get content type
        content_type = self.headers.get('Content-Type', '')
        
        # Debug information
        print(f"POST to {self.path} with content type: {content_type}, length: {content_length}")
        
        # Parse POST data based on content type
        post_data = {}
        
        if content_length > 0:
            if "application/json" in content_type:
                # Handle JSON data
                post_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
                print(f"Parsed JSON data: {post_data}")
            elif "multipart/form-data" in content_type:
                # For multipart form data (like file uploads), will be handled in specific endpoints
                print("Multipart form data detected, will handle in endpoint")
            else:
                # Handle plain form data (url-encoded)
                form_data = self.rfile.read(content_length).decode('utf-8')
                post_data = parse_qs(form_data)
                for key in post_data:
                    post_data[key] = post_data[key][0]
                print(f"Parsed form data: {post_data}")
        
        # Process based on path
        path = self.path
        
        # Register user
        if path == '/register':
            if not post_data:
                self._set_response(400)
                self.wfile.write(json_dumps({"error": "Missing registration data"}).encode())
                return
            
            print(f"Registration data: {post_data}")
            
            # Check required fields
            required_fields = ['name', 'email', 'password']
            missing_fields = [field for field in required_fields if field not in post_data]
            
            if missing_fields:
                self._set_response(400)
                self.wfile.write(json_dumps({"error": f"Missing required fields: {', '.join(missing_fields)}"}).encode())
                return
            
            # Register the user
            response = register_user(
                post_data['name'], 
                post_data['email'], 
                post_data['password'],
                post_data.get('phone', '')  # Optional field
            )
            
            if "error" in response:
                self._set_response(400)
            else:
                self._set_response(201)
            
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Register artist
        elif path == '/register-artist':
            if not post_data:
                self._set_response(400)
                self.wfile.write(json_dumps({"error": "Missing registration data"}).encode())
                return
            
            # Check required fields
            required_fields = ['name', 'email', 'password']
            missing_fields = [field for field in required_fields if field not in post_data]
            
            if missing_fields:
                self._set_response(400)
                self.wfile.write(json_dumps({"error": f"Missing required fields: {', '.join(missing_fields)}"}).encode())
                return
            
            # Register the artist
            response = register_artist(
                post_data['name'], 
                post_data['email'], 
                post_data['password'],
                post_data.get('phone', ''),  # Optional field
                post_data.get('bio', '')     # Optional field
            )
            
            if "error" in response:
                self._set_response(400)
            else:
                self._set_response(201)
            
            self.wfile.write(json_dumps(response).encode())
            return
        
        # User login
        elif path == '/login':
            if not post_data:
                self._set_response(400)
                self.wfile.write(json_dumps({"error": "Missing login data"}).encode())
                return
            
            # Check required fields
            if 'email' not in post_data or 'password' not in post_data:
                self._set_response(400)
                self.wfile.write(json_dumps({"error": "Email and password required"}).encode())
                return
            
            # Login the user
            response = login_user(post_data['email'], post_data['password'])
            
            if "error" in response:
                self._set_response(401)
                self.wfile.write(json_dumps(response).encode())
                return
            
            self._set_response(200)
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Artist login
        elif path == '/artist-login':
            if not post_data:
                self._set_response(400)
                self.wfile.write(json_dumps({"error": "Missing login data"}).encode())
                return
            
            # Check required fields
            if 'email' not in post_data or 'password' not in post_data:
                self._set_response(400)
                self.wfile.write(json_dumps({"error": "Email and password required"}).encode())
                return
            
            # Login the artist
            response = login_artist(post_data['email'], post_data['password'])
            
            if "error" in response:
                self._set_response(401)
                self.wfile.write(json_dumps(response).encode())
                return
            
            self._set_response(200)
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Admin login - Fixed the endpoint
        elif path == '/admin-login':
            if not post_data:
                self._set_response(400)
                self.wfile.write(json_dumps({"error": "Missing login data"}).encode())
                return
            
            # Check required fields
            if 'email' not in post_data or 'password' not in post_data:
                self._set_response(400)
                self.wfile.write(json_dumps({"error": "Email and password required"}).encode())
                return
            
            # Login as admin
            response = login_admin(post_data['email'], post_data['password'])
            
            if "error" in response:
                self._set_response(401)
                self.wfile.write(json_dumps(response).encode())
                return
            
            self._set_response(200)
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Add 2FA endpoints for backward compatibility (though not used)
        elif path == '/send-2fa-code':
            # Return success for backward compatibility
            self._set_response(200)
            self.wfile.write(json_dumps({"success": True, "message": "2FA disabled"}).encode())
            return
            
        elif path == '/verify-2fa':
            # Return success for backward compatibility
            self._set_response(200)
            self.wfile.write(json_dumps({"verified": True}).encode())
            return
        
        # Create artwork (admin or artist)
        elif path == '/artworks':
            auth_header = self.headers.get('Authorization', '')
            token = extract_auth_token(auth_header)
            
            if not token:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": "Authentication required"}).encode())
                return
            
            payload = verify_token(token)
            if isinstance(payload, dict) and "error" in payload:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": payload["error"]}).encode())
                return
            
            # Check if user is admin or artist
            if not (payload.get("is_admin", False) or payload.get("is_artist", False)):
                self._set_response(403)
                self.wfile.write(json_dumps({"error": "Unauthorized: Admin or artist privileges required"}).encode())
                return
            
            # Add artist_id to the post_data if the request is from an artist
            if payload.get("is_artist", False):
                post_data["artist_id"] = payload.get("sub")
            
            # Create artwork
            response = create_artwork(auth_header, post_data)
            
            if "error" in response:
                error_message = response["error"]
                
                if "Authentication" in error_message or "authorized" in error_message:
                    self._set_response(401)
                elif "Admin" in error_message:
                    self._set_response(403)
                else:
                    self._set_response(400)
                    
                self.wfile.write(json_dumps({"error": error_message}).encode())
                return
            
            self._set_response(201)
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Create exhibition (admin only)
        elif path == '/exhibitions':
            auth_header = self.headers.get('Authorization', '')
            response = create_exhibition(auth_header, post_data)
            
            if "error" in response:
                error_message = response["error"]
                
                if "Authentication" in error_message or "authorized" in error_message:
                    self._set_response(401)
                elif "Admin" in error_message:
                    self._set_response(403)
                else:
                    self._set_response(400)
                    
                self.wfile.write(json_dumps({"error": error_message}).encode())
                return
            
            self._set_response(201)
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Create contact message
        elif path == '/contact':
            response = create_contact_message(post_data)
            
            if "error" in response:
                self._set_response(400)
            else:
                self._set_response(201)
            
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Update message status (admin only)
        elif path.startswith('/messages/'):
            message_id = path.split('/')[2]
            token = extract_auth_token(self)
            if not token:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": "Authentication required"}).encode())
                return
            
            payload = verify_token(token)
            if isinstance(payload, dict) and "error" in payload:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": payload["error"]}).encode())
                return
            
            # Check if user is admin
            if not payload.get("is_admin", False):
                self._set_response(403)
                self.wfile.write(json_dumps({"error": "Unauthorized access: Admin privileges required"}).encode())
                return
            
            response = update_message(self.headers.get('Authorization', ''), message_id, post_data)
            
            if "error" in response:
                self._set_response(400)
            else:
                self._set_response(200)
            
            self.wfile.write(json_dumps(response).encode())
            return
        
        # New M-Pesa STK Push endpoint
        elif path == '/mpesa/stk-push':
            print("Processing M-Pesa STK Push request")
            response = handle_stk_push_request(post_data)
            
            if "error" in response:
                self._set_response(400)
                self.wfile.write(json_dumps(response).encode())
                return
            
            self._set_response(200)
            self.wfile.write(json_dumps(response).encode())
            return
            
        # M-Pesa callback endpoint
        elif path == '/mpesa/callback':
            print("Processing M-Pesa callback")
            response = handle_mpesa_callback(post_data)
            
            if "error" in response:
                self._set_response(400)
                self.wfile.write(json_dumps(response).encode())
                return
            
            self._set_response(200)
            self.wfile.write(json_dumps(response).encode())
            return
            
        # M-Pesa transaction status check endpoint
        elif path.startswith('/mpesa/status/'):
            checkout_request_id = path.split('/')[3]
            print(f"Checking M-Pesa transaction status for: {checkout_request_id}")
            
            response = check_transaction_status(checkout_request_id)
            
            if "error" in response:
                self._set_response(400)
                self.wfile.write(json_dumps(response).encode())
                return
            
            self._set_response(200)
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Default 404 response
        self._set_response(404)
        self.wfile.write(json_dumps({"error": "Resource not found"}).encode())
    
    def do_PUT(self):
        # Get content length
        content_length = int(self.headers.get('Content-Length', 0))
        
        # Parse JSON data
        post_data = {}
        if content_length > 0:
            post_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        
        # Process based on path
        path = self.path
        
        # Update artwork (admin or artist)
        if path.startswith('/artworks/') and len(path.split('/')) == 3:
            artwork_id = path.split('/')[2]
            auth_header = self.headers.get('Authorization', '')
            
            # Extract token and verify
            token = extract_auth_token(auth_header)
            
            if not token:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": "Authentication required"}).encode())
                return
            
            payload = verify_token(token)
            if isinstance(payload, dict) and "error" in payload:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": payload["error"]}).encode())
                return
            
            # Check if user is admin or the artist who created the artwork
            is_admin = payload.get("is_admin", False)
            is_artist = payload.get("is_artist", False)
            artist_id = payload.get("sub")
            
            if not is_admin and is_artist:
                # Verify if the artist owns this artwork
                connection = get_db_connection()
                if connection is None:
                    self._set_response(500)
                    self.wfile.write(json_dumps({"error": "Database connection failed"}).encode())
                    return
                
                cursor = connection.cursor()
                try:
                    # Check both artist_id and artist name for ownership
                    cursor.execute("""
                        SELECT a.id FROM artworks a
                        JOIN artists art ON art.id = %s
                        WHERE a.id = %s AND (a.artist_id = %s OR a.artist = art.name)
                    """, (artist_id, artwork_id, artist_id))
                    
                    result = cursor.fetchone()
                    
                    if not result:
                        self._set_response(403)
                        self.wfile.write(json_dumps({"error": "Unauthorized: You can only update your own artworks"}).encode())
                        return
                finally:
                    cursor.close()
                    connection.close()
            
            # If admin or verified artist, update artwork
            response = update_artwork(auth_header, artwork_id, post_data)
            
            if "error" in response:
                error_message = response["error"]
                
                if "Authentication" in error_message or "authorized" in error_message:
                    self._set_response(401)
                elif "Admin" in error_message:
                    self._set_response(403)
                elif "not found" in error_message:
                    self._set_response(404)
                else:
                    self._set_response(400)
                    
                self.wfile.write(json_dumps({"error": error_message}).encode())
                return
            
            self._set_response(200)
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Update exhibition (admin only)
        elif path.startswith('/exhibitions/') and len(path.split('/')) == 3:
            exhibition_id = path.split('/')[2]
            auth_header = self.headers.get('Authorization', '')
            
            response = update_exhibition(auth_header, exhibition_id, post_data)
            
            if "error" in response:
                error_message = response["error"]
                
                if "Authentication" in error_message or "authorized" in error_message:
                    self._set_response(401)
                elif "Admin" in error_message:
                    self._set_response(403)
                elif "not found" in error_message:
                    self._set_response(404)
                else:
                    self._set_response(400)
                    
                self.wfile.write(json_dumps({"error": error_message}).encode())
                return
            
            self._set_response(200)
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Default 404 response
        self._set_response(404)
        self.wfile.write(json_dumps({"error": "Resource not found"}).encode())
    
    def do_DELETE(self):
        # Process based on path
        path = self.path
        
        # Delete artwork (admin or artist)
        if path.startswith('/artworks/') and len(path.split('/')) == 3:
            artwork_id = path.split('/')[2]
            auth_header = self.headers.get('Authorization', '')
            
            # Extract token and verify
            token = extract_auth_token(auth_header)
            
            if not token:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": "Authentication required"}).encode())
                return
            
            payload = verify_token(token)
            if isinstance(payload, dict) and "error" in payload:
                self._set_response(401)
                self.wfile.write(json_dumps({"error": payload["error"]}).encode())
                return
            
            # Check if user is admin or the artist who created the artwork
            is_admin = payload.get("is_admin", False)
            is_artist = payload.get("is_artist", False)
            artist_id = payload.get("sub")
            
            if not is_admin and is_artist:
                # Verify if the artist owns this artwork
                connection = get_db_connection()
                if connection is None:
                    self._set_response(500)
                    self.wfile.write(json_dumps({"error": "Database connection failed"}).encode())
                    return
                
                cursor = connection.cursor()
                try:
                    # Check both artist_id and artist name for ownership
                    cursor.execute("""
                        SELECT a.id FROM artworks a
                        JOIN artists art ON art.id = %s
                        WHERE a.id = %s AND (a.artist_id = %s OR a.artist = art.name)
                    """, (artist_id, artwork_id, artist_id))
                    
                    result = cursor.fetchone()
                    
                    if not result:
                        self._set_response(403)
                        self.wfile.write(json_dumps({"error": "Unauthorized: You can only delete your own artworks"}).encode())
                        return
                finally:
                    cursor.close()
                    connection.close()
            
            # If admin or verified artist, delete artwork
            response = delete_artwork(auth_header, artwork_id)
            
            if "error" in response:
                error_message = response["error"]
                
                if "Authentication" in error_message or "authorized" in error_message:
                    self._set_response(401)
                elif "Admin" in error_message:
                    self._set_response(403)
                elif "not found" in error_message:
                    self._set_response(404)
                else:
                    self._set_response(400)
                    
                self.wfile.write(json_dumps({"error": error_message}).encode())
                return
            
            self._set_response(200)
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Delete exhibition (admin only)
        elif path.startswith('/exhibitions/') and len(path.split('/')) == 3:
            exhibition_id = path.split('/')[2]
            auth_header = self.headers.get('Authorization', '')
            
            response = delete_exhibition(auth_header, exhibition_id)
            
            if "error" in response:
                error_message = response["error"]
                
                if "Authentication" in error_message or "authorized" in error_message:
                    self._set_response(401)
                elif "Admin" in error_message:
                    self._set_response(403)
                elif "not found" in error_message:
                    self._set_response(404)
                else:
                    self._set_response(400)
                    
                self.wfile.write(json_dumps({"error": error_message}).encode())
                return
            
            self._set_response(200)
            self.wfile.write(json_dumps(response).encode())
            return
        
        # Default 404 response
        self._set_response(404)
        self.wfile.write(json_dumps({"error": "Resource not found"}).encode())

def main():
    """Start the server"""
    # Initialize the database
    print("Initializing database...")
    initialize_database()
    
    # Create uploads directory if it doesn't exist
    ensure_uploads_directory()
    
    # Create placeholder and default images
    create_placeholder_svg()
    create_default_exhibition_image()
    
    # Create an HTTP server
    print(f"Starting server on port {PORT}...")
    httpd = socketserver.ThreadingTCPServer(("", PORT), RequestHandler)
    print(f"Server running on port {PORT}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        httpd.server_close()
        print("Server closed")

if __name__ == "__main__":
    main()
