from database import get_db_connection, dict_from_row, json_dumps
from auth import verify_token
import json
import os
import base64
import time
from decimal import Decimal

# Create the uploads directory if it doesn't exist
def ensure_uploads_directory():
    """Create the uploads directory if it doesn't exist"""
    uploads_dir = os.path.join(os.path.dirname(__file__), "static", "uploads")
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        print(f"Created directory: {uploads_dir}")

# Call this function to ensure directory exists
ensure_uploads_directory()

# Function to handle image storage
def save_image_from_base64(base64_str, name_prefix="artwork"):
    """Save a base64 image to the uploads directory and return the path"""
    if not base64_str:
        return None
        
    # If it's already a URL path (not base64), return it as is
    if base64_str.startswith('/static/'):
        return base64_str
    
    try:
        # Extract the image data from the base64 string
        if "," in base64_str:
            # For format like "data:image/jpeg;base64,/9j/4AAQSk..."
            image_format, base64_data = base64_str.split(",", 1)
            if ';base64' not in image_format:
                print("Warning: Not a valid base64 image format")
                return None
        else:
            # Assume it's just the base64 data
            base64_data = base64_str
        
        try:
            # Decode the base64 data
            image_data = base64.b64decode(base64_data)
        except Exception as e:
            print(f"Failed to decode base64 data: {e}")
            return "/static/uploads/placeholder.jpg"
        
        # Generate a unique filename based on timestamp
        timestamp = time.strftime("%Y%m%d%H%M%S")
        filename = f"{name_prefix}_{timestamp}.jpg"
        
        # Save to the uploads directory
        uploads_dir = os.path.join(os.path.dirname(__file__), "static", "uploads")
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            
        file_path = os.path.join(uploads_dir, filename)
        with open(file_path, "wb") as f:
            f.write(image_data)
        
        # Return the URL path to the image (ALWAYS use the standard format)
        return f"/static/uploads/{filename}"
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

def get_all_artworks():
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    
    try:
        query = """
        SELECT id, title, artist, description, price, image_url, 
               dimensions, medium, year, status
        FROM artworks
        ORDER BY created_at DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        artworks = []
        for row in rows:
            artwork = dict_from_row(row, cursor)
            
            # Convert id to string to match frontend expectations
            artwork['id'] = str(artwork['id'])
            
            # Format image URL if needed - ALWAYS ensure it has the correct prefix
            if artwork['image_url']:
                # Handle base64 images
                if artwork['image_url'].startswith('data:') or 'base64' in artwork['image_url']:
                    # Save the base64 image to a file and get its path
                    saved_path = save_image_from_base64(artwork['image_url'])
                    if saved_path:
                        # Update the database with the new path
                        update_artwork_image(artwork['id'], saved_path)
                        artwork['image_url'] = saved_path
                        print(f"Converted base64 image to file: {saved_path}")
                elif not artwork['image_url'].startswith('/static/'):
                    artwork['image_url'] = f"/static/uploads/{os.path.basename(artwork['image_url'])}"
                
                # Log the final image URL for debugging
                print(f"Final image URL for {artwork['title']}: {artwork['image_url']}")
                
            artworks.append(artwork)
        
        return {"artworks": artworks}
    except Exception as e:
        print(f"Error getting artworks: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_artwork_image(artwork_id, image_path):
    connection = get_db_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    try:
        query = """
        UPDATE artworks
        SET image_url = %s
        WHERE id = %s
        """
        cursor.execute(query, (image_path, artwork_id))
        connection.commit()
        return True
    except Exception as e:
        print(f"Error updating artwork image: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_artwork(artwork_id):
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    
    try:
        query = """
        SELECT id, title, artist, description, price, image_url, 
               dimensions, medium, year, status
        FROM artworks
        WHERE id = %s
        """
        cursor.execute(query, (artwork_id,))
        row = cursor.fetchone()
        
        if not row:
            return {"error": "Artwork not found"}
        
        artwork = dict_from_row(row, cursor)
        # Convert id to string to match frontend expectations
        artwork['id'] = str(artwork['id'])
        
        # Format image URL if needed
        if artwork['image_url']:
            # Handle base64 images
            if artwork['image_url'].startswith('data:') or artwork['image_url'].startswith('base64,'):
                # Save the base64 image to a file and get the file path
                saved_path = save_image_from_base64(artwork['image_url'])
                if saved_path:
                    # Update the database with the new path
                    update_artwork_image(artwork['id'], saved_path)
                    artwork['image_url'] = saved_path
                    print(f"Converted base64 image to file: {saved_path}")
            elif not artwork['image_url'].startswith('/static/'):
                artwork['image_url'] = f"/static/uploads/{os.path.basename(artwork['image_url'])}"
        
        return artwork
    except Exception as e:
        print(f"Error getting artwork: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def create_artwork(auth_header, artwork_data):
    """Create a new artwork (admin or artist only)"""
    print(f"\n--- Create Artwork Request ---")
    print(f"Auth Header: {auth_header}")
    print(f"Artwork Data: {artwork_data}")
    
    if not auth_header:
        print("ERROR: Authentication header missing")
        return {"error": "Authentication required"}
    
    # Extract token from header - handle both formats
    token = None
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    else:
        parts = auth_header.split(" ")
        if len(parts) > 1:
            token = parts[1]
    
    if not token:
        print("ERROR: No token found in header")
        return {"error": "Invalid authentication token"}
    
    # Verify token and check if user is admin or artist
    print(f"Verifying token: {token[:20]}...")
    payload = verify_token(token)
    print(f"Token verification result: {payload}")
    
    # Check if verification returned an error
    if isinstance(payload, dict) and "error" in payload:
        print(f"ERROR: Token verification failed: {payload['error']}")
        return {"error": f"Authentication failed: {payload['error']}"}
    
    # Check if user is admin or artist
    is_admin = payload.get("is_admin", False)
    is_artist = payload.get("is_artist", False)
    artist_id = payload.get("sub") if is_artist else None
    print(f"Is admin: {is_admin}, Is artist: {is_artist}, Artist ID: {artist_id}")
    
    if not (is_admin or is_artist):
        print("ERROR: Access denied - Neither admin nor artist")
        return {"error": "Unauthorized access: Admin or artist privileges required"}
    
    # Continue with artwork creation
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    
    try:
        # Parse artwork_data if it's a string
        if isinstance(artwork_data, str):
            try:
                artwork_data = json.loads(artwork_data)
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to parse artwork data: {e}")
                return {"error": f"Invalid artwork data format: {str(e)}"}
        
        # Handle the image - convert base64 to file if needed
        image_url = artwork_data.get("imageUrl")
        if image_url and (image_url.startswith('data:') or image_url.startswith('base64,')):
            # Save the image and get the file path
            saved_image_path = save_image_from_base64(image_url)
            if saved_image_path:
                image_url = saved_image_path
                print(f"Image saved to: {saved_image_path}")
            else:
                print("Failed to save image")
                image_url = "/placeholder.svg"
        
        # If artist is creating artwork, use their name from token
        if is_artist and not is_admin:
            artist_name = payload.get("name", artwork_data.get("artist", "Unknown Artist"))
            artwork_data["artist"] = artist_name
            # Make sure we set the artist_id in the database
            artwork_data["artist_id"] = artist_id
        
        print(f"Inserting artwork data: {artwork_data}")
        query = """
        INSERT INTO artworks (title, artist, description, price, image_url,
                           dimensions, medium, year, status, artist_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            artwork_data.get("title"),
            artwork_data.get("artist"),
            artwork_data.get("description"),
            artwork_data.get("price"),
            image_url,
            artwork_data.get("dimensions"),
            artwork_data.get("medium"),
            artwork_data.get("year"),
            artwork_data.get("status", "available"),
            artwork_data.get("artist_id", artist_id)  # Use artist_id from token if available
        ))
        connection.commit()
        
        # Return the newly created artwork
        new_artwork_id = cursor.lastrowid
        print(f"Artwork created successfully with ID: {new_artwork_id}")
        return get_artwork(new_artwork_id)
    except Exception as e:
        print(f"ERROR creating artwork: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_artwork(auth_header, artwork_id, artwork_data):
    """Update an existing artwork (admin or artist who owns it)"""
    if not auth_header:
        return {"error": "Authentication required"}
    
    # Extract token from header
    token = None
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    else:
        parts = auth_header.split(" ")
        if len(parts) > 1:
            token = parts[1]
    
    if not token:
        return {"error": "Invalid authentication token"}
    
    # Debug token verification
    print(f"Verifying token for update_artwork: {token[:20]}...")
    
    # Verify token and check if user is admin
    payload = verify_token(token)
    print(f"Token verification result: {payload}")
    
    # Check if verification returned an error
    if isinstance(payload, dict) and "error" in payload:
        return {"error": f"Token verification failed: {payload['error']}"}
    
    # Check if user is admin or artist
    is_admin = payload.get("is_admin", False)
    is_artist = payload.get("is_artist", False)
    artist_id = payload.get("sub") if is_artist else None
    
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    
    try:
        # First check if artist is the owner (or admin)
        if is_artist and not is_admin:
            check_query = "SELECT artist_id FROM artworks WHERE id = %s"
            cursor.execute(check_query, (artwork_id,))
            result = cursor.fetchone()
            if not result or str(result[0]) != str(artist_id):
                return {"error": "Unauthorized access: You can only edit your own artworks"}
        elif not is_admin:  # Not artist and not admin
            return {"error": "Unauthorized access: Not authorized"}
            
        # Handle the image - convert base64 to file if needed
        image_url = artwork_data.get("imageUrl")
        if image_url and (image_url.startswith('data:') or image_url.startswith('base64,')):
            # Save the image and get the file path
            saved_image_path = save_image_from_base64(image_url)
            if saved_image_path:
                image_url = saved_image_path
                print(f"Image saved to: {saved_image_path}")
            else:
                print("Failed to save image")
                # Keep the original image URL if saving fails
                cursor.execute("SELECT image_url FROM artworks WHERE id = %s", (artwork_id,))
                result = cursor.fetchone()
                if result:
                    image_url = result[0]
                else:
                    image_url = "/placeholder.svg"
                    
        query = """
        UPDATE artworks
        SET title = %s, artist = %s, description = %s, price = %s,
            image_url = %s, dimensions = %s, medium = %s, year = %s, status = %s
        WHERE id = %s
        """
        cursor.execute(query, (
            artwork_data.get("title"),
            artwork_data.get("artist"),
            artwork_data.get("description"),
            artwork_data.get("price"),
            image_url,
            artwork_data.get("dimensions"),
            artwork_data.get("medium"),
            artwork_data.get("year"),
            artwork_data.get("status"),
            artwork_id
        ))
        connection.commit()
        
        # Check if artwork was found and updated
        if cursor.rowcount == 0:
            return {"error": "Artwork not found"}
        
        # Return the updated artwork
        return get_artwork(artwork_id)
    except Exception as e:
        print(f"Error updating artwork: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_artwork(auth_header, artwork_id):
    """Delete an artwork (admin or artist who owns it)"""
    if not auth_header:
        return {"error": "Authentication required"}
    
    # Extract token from header
    token = None
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    else:
        parts = auth_header.split(" ")
        if len(parts) > 1:
            token = parts[1]
    
    if not token:
        return {"error": "Invalid authentication token"}
    
    # Debug token verification
    print(f"Verifying token for delete_artwork: {token[:20]}...")
    
    # Verify token and check if user is admin or artist
    payload = verify_token(token)
    print(f"Token verification result: {payload}")
    
    # Check if verification returned an error
    if isinstance(payload, dict) and "error" in payload:
        return {"error": f"Token verification failed: {payload['error']}"}
    
    # Check if user is admin or artist
    is_admin = payload.get("is_admin", False)
    is_artist = payload.get("is_artist", False)
    artist_id = payload.get("sub") if is_artist else None
    
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    
    try:
        # First check if artist is the owner (or admin)
        if is_artist and not is_admin:
            check_query = "SELECT artist_id FROM artworks WHERE id = %s"
            cursor.execute(check_query, (artwork_id,))
            result = cursor.fetchone()
            if not result or str(result[0]) != str(artist_id):
                return {"error": "Unauthorized access: You can only delete your own artworks"}
                
        query = "DELETE FROM artworks WHERE id = %s"
        cursor.execute(query, (artwork_id,))
        connection.commit()
        
        # Check if artwork was found and deleted
        if cursor.rowcount == 0:
            return {"error": "Artwork not found"}
        
        return {"success": True, "message": "Artwork deleted successfully"}
    except Exception as e:
        print(f"Error deleting artwork: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
