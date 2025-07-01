// API service to connect to the Python backend

// Base URL for the API
const API_URL = 'http://localhost:8000';

// Interface for auth responses
interface AuthResponse {
  token?: string;
  user_id?: number;
  admin_id?: number;
  artist_id?: number;
  name?: string;
  error?: string;
}

// Interface for login data
interface LoginData {
  email: string;
  password: string;
}

// Interface for registration data
interface RegisterData {
  name: string;
  email: string;
  password: string;
  phone: string;
  bio?: string; // Optional for artist registration
}

// Interface for artwork data
export interface ArtworkData {
  id?: string;
  title: string;
  artist: string;
  artist_id?: number;
  description: string;
  price: number;
  imageUrl: string;
  dimensions?: string;
  medium?: string;
  year?: number;
  status: 'available' | 'sold';
}

// Interface for exhibition data
export interface ExhibitionData {
  id?: string;
  title: string;
  description: string;
  location: string;
  startDate: string;
  endDate: string;
  ticketPrice: number;
  imageUrl: string;
  totalSlots: number;
  availableSlots: number;
  status: 'upcoming' | 'ongoing' | 'past';
}

// Interface for contact message
interface ContactMessage {
  name: string;
  email: string;
  phone?: string;
  message: string;
  source?: string; // Added source field
}

// Interface for artist data
export interface ArtistData {
  id: number;
  name: string;
  email: string;
  bio: string;
  profile_image_url: string;
  phone: string;
  created_at: string;
  artwork_count: number;
}

// Helper function to store auth data
const storeAuthData = (data: AuthResponse, isAdmin: boolean, isArtist: boolean = false) => {
  if (data.token) {
    localStorage.setItem('token', data.token);
    localStorage.setItem('userName', data.name || '');
    localStorage.setItem('isAdmin', isAdmin ? 'true' : 'false');
    localStorage.setItem('isArtist', isArtist ? 'true' : 'false');
    
    // Store user, admin, or artist ID
    if (data.user_id) {
      localStorage.setItem('userId', data.user_id.toString());
    } else if (data.admin_id) {
      localStorage.setItem('adminId', data.admin_id.toString());
    } else if (data.artist_id) {
      localStorage.setItem('artistId', data.artist_id.toString());
    }
    
    return true;
  }
  
  return false;
};

// Register a new user
export const registerUser = async (userData: RegisterData): Promise<AuthResponse> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    const response = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    const data = await response.json();
    
    if (response.ok) {
      storeAuthData(data, false);
    }
    
    return data;
  } catch (error) {
    console.error('Registration error:', error);
    if (error instanceof DOMException && error.name === 'AbortError') {
      return { error: 'Connection timeout. Server may be down or unreachable.' };
    }
    return { error: 'Network error. Please try again.' };
  }
};

// Register a new artist
export const registerArtist = async (artistData: RegisterData): Promise<AuthResponse> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    const response = await fetch(`${API_URL}/register-artist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(artistData),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    const data = await response.json();
    
    if (response.ok) {
      storeAuthData(data, false, true);
    }
    
    return data;
  } catch (error) {
    console.error('Artist registration error:', error);
    if (error instanceof DOMException && error.name === 'AbortError') {
      return { error: 'Connection timeout. Server may be down or unreachable.' };
    }
    return { error: 'Network error. Please try again.' };
  }
};

// Login a user
export const loginUser = async (credentials: LoginData): Promise<AuthResponse> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    const data = await response.json();
    
    if (response.ok) {
      storeAuthData(data, false);
    }
    
    return data;
  } catch (error) {
    console.error('Login error:', error);
    if (error instanceof DOMException && error.name === 'AbortError') {
      return { error: 'Connection timeout. Server may be down or unreachable.' };
    }
    return { error: 'Network error. Please try again.' };
  }
};

// Login as artist
export const loginArtist = async (credentials: LoginData): Promise<AuthResponse> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    const response = await fetch(`${API_URL}/artist-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    const data = await response.json();
    
    if (response.ok) {
      storeAuthData(data, false, true);
    }
    
    return data;
  } catch (error) {
    console.error('Artist login error:', error);
    if (error instanceof DOMException && error.name === 'AbortError') {
      return { error: 'Connection timeout. Server may be down or unreachable.' };
    }
    return { error: 'Network error. Please try again.' };
  }
};

// Login as admin
export const loginAdmin = async (credentials: LoginData): Promise<AuthResponse> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    const response = await fetch(`${API_URL}/admin-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    const data = await response.json();
    
    if (response.ok) {
      console.log("Admin login successful, storing data:", {
        ...data,
        token: data.token ? `${data.token.substring(0, 20)}...` : null
      });
      storeAuthData(data, true);
    } else {
      console.error("Admin login failed:", data.error);
    }
    
    return data;
  } catch (error) {
    console.error('Admin login error:', error);
    if (error instanceof DOMException && error.name === 'AbortError') {
      return { error: 'Connection timeout. Server may be down or unreachable.' };
    }
    return { error: 'Network error. Please try again.' };
  }
};

// Get the auth token
export const getToken = (): string | null => {
  return localStorage.getItem('token');
};

// Check if user is authenticated
export const isAuthenticated = (): boolean => {
  return !!getToken();
};

// Check if user is an admin
export const isAdmin = (): boolean => {
  return localStorage.getItem('isAdmin') === 'true';
};

// Check if user is an artist
export const isArtist = (): boolean => {
  return localStorage.getItem('isArtist') === 'true';
};

// Get artist ID
export const getArtistId = (): string | null => {
  return localStorage.getItem('artistId');
};

// Logout user
export const logout = (): void => {
  localStorage.removeItem('token');
  localStorage.removeItem('userName');
  localStorage.removeItem('isAdmin');
  localStorage.removeItem('isArtist');
  localStorage.removeItem('userId');
  localStorage.removeItem('adminId');
  localStorage.removeItem('artistId');
};

// API request with authentication
export const authFetch = async (url: string, options: RequestInit = {}): Promise<any> => {
  const token = getToken();
  
  if (!token) {
    console.error('No authentication token found');
    throw new Error('No authentication token found');
  }
  
  // Ensure correct Authorization header format
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
    
    console.log(`Making authenticated request to: ${API_URL}${url}`);
    console.log('Using token:', token.substring(0, 20) + '...');
    console.log('Request options:', { 
      ...options, 
      headers: { ...headers, Authorization: 'Bearer [REDACTED]' } 
    });
    
    const response = await fetch(`${API_URL}${url}`, {
      ...options,
      headers,
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    let data;
    // Parse response based on content type
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      const text = await response.text();
      try {
        data = JSON.parse(text);
      } catch (e) {
        data = { text };
      }
    }
    
    console.log('Response status:', response.status);
    console.log('Response data:', data);
    
    // Handle different status codes
    if (response.status === 401) {
      // Token expired or invalid
      console.error('401 Unauthorized error - Token invalid or expired', data);
      throw new Error('Session expired. Please login again.');
    }
    
    if (response.status === 403) {
      console.error('403 Forbidden error - Access denied', data);
      throw new Error(data.error || 'Access denied. Please check your permissions.');
    }
    
    if (!response.ok) {
      throw new Error(data.error || `Request failed with status ${response.status}`);
    }
    
    return data;
  } catch (error) {
    console.error('API request error:', error);
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('Connection timeout. Server may be down or unreachable.');
    }
    throw error;
  }
};

// Create a new artwork (admin or artist)
export const createArtwork = async (artworkData: ArtworkData) => {
  console.log('Creating artwork with data:', artworkData);
  return await authFetch('/artworks', {
    method: 'POST',
    body: JSON.stringify(artworkData),
  });
};

// Update existing artwork (admin or artist)
export const updateArtwork = async (id: string, artworkData: ArtworkData) => {
  console.log(`Updating artwork ${id} with data:`, artworkData);
  return await authFetch(`/artworks/${id}`, {
    method: 'PUT',
    body: JSON.stringify(artworkData),
  });
};

// Delete artwork (admin or artist)
export const deleteArtwork = async (id: string) => {
  console.log(`Deleting artwork ${id}`);
  return await authFetch(`/artworks/${id}`, {
    method: 'DELETE',
  });
};

// Create a new exhibition (admin only)
export const createExhibition = async (exhibitionData: ExhibitionData) => {
  console.log('Creating exhibition with data:', exhibitionData);
  return await authFetch('/exhibitions', {
    method: 'POST',
    body: JSON.stringify(exhibitionData),
  });
};

// Update existing exhibition (admin only)
export const updateExhibition = async (id: string, exhibitionData: ExhibitionData) => {
  console.log(`Updating exhibition ${id} with data:`, exhibitionData);
  return await authFetch(`/exhibitions/${id}`, {
    method: 'PUT',
    body: JSON.stringify(exhibitionData),
  });
};

// Delete exhibition (admin only)
export const deleteExhibition = async (id: string) => {
  console.log(`Deleting exhibition ${id}`);
  return await authFetch(`/exhibitions/${id}`, {
    method: 'DELETE',
  });
};

// Get all artworks
export const getAllArtworks = async () => {
  try {
    const response = await fetch(`${API_URL}/artworks`);
    if (!response.ok) {
      throw new Error('Failed to fetch artworks');
    }
    const data = await response.json();
    return data.artworks || [];
  } catch (error) {
    console.error('Error fetching artworks:', error);
    throw error;
  }
};

// Get a single artwork
export const getArtwork = async (id: string) => {
  try {
    const response = await fetch(`${API_URL}/artworks/${id}`);
    if (!response.ok) {
      throw new Error('Failed to fetch artwork');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching artwork:', error);
    throw error;
  }
};

// Get all artist's artworks
export const getArtistArtworks = async () => {
  try {
    return await authFetch('/artist/artworks');
  } catch (error) {
    console.error('Error fetching artist artworks:', error);
    throw error;
  }
};

// Get all artist's orders
export const getArtistOrders = async () => {
  try {
    return await authFetch('/artist/orders');
  } catch (error) {
    console.error('Error fetching artist orders:', error);
    throw error;
  }
};

// Get all artists (admin only)
export const getAllArtists = async () => {
  try {
    return await authFetch('/artists');
  } catch (error) {
    console.error('Error fetching artists:', error);
    throw error;
  }
};

// Get all exhibitions
export const getAllExhibitions = async () => {
  try {
    const response = await fetch(`${API_URL}/exhibitions`);
    if (!response.ok) {
      throw new Error('Failed to fetch exhibitions');
    }
    const data = await response.json();
    return data.exhibitions || [];
  } catch (error) {
    console.error('Error fetching exhibitions:', error);
    throw error;
  }
};

// Get a single exhibition
export const getExhibition = async (id: string) => {
  try {
    const response = await fetch(`${API_URL}/exhibitions/${id}`);
    if (!response.ok) {
      throw new Error('Failed to fetch exhibition');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching exhibition:', error);
    throw error;
  }
};

// Submit a contact message
export const submitContactMessage = async (messageData: ContactMessage) => {
  try {
    const response = await fetch(`${API_URL}/contact`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(messageData),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to submit contact message');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error submitting contact message:', error);
    throw error;
  }
};

// Get all contact messages (admin only)
export const getAllContactMessages = async () => {
  console.log("Fetching all contact messages with auth token");
  try {
    const result = await authFetch('/messages');
    console.log("Contact messages result:", result);
    return result;
  } catch (error) {
    console.error("Error fetching contact messages:", error);
    throw error;
  }
};

// Update message status (admin only)
export const updateMessageStatus = async (id: string, status: 'new' | 'read' | 'replied') => {
  console.log(`Updating message ${id} status to ${status}`);
  return await authFetch(`/messages/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ status }),
  });
};

// Place an order for artwork
export const placeArtworkOrder = async (orderData: any) => {
  return await authFetch('/orders/artwork', {
    method: 'POST',
    body: JSON.stringify(orderData),
  });
};

// Book an exhibition
export const bookExhibition = async (bookingData: any) => {
  return await authFetch('/orders/exhibition', {
    method: 'POST',
    body: JSON.stringify(bookingData),
  });
};

// Get all tickets (admin only)
export const getAllTickets = async () => {
  return await authFetch('/tickets');
};

// Get all orders (admin only)
export const getAllOrders = async () => {
  return await authFetch('/orders');
};

// Generate exhibition ticket
export const generateExhibitionTicket = async (bookingId: string) => {
  try {
    return await authFetch(`/tickets/generate/${bookingId}`);
  } catch (error) {
    console.error('Ticket generation error:', error);
    throw error;
  }
};

// Get user tickets
export const getUserTickets = async (userId: string) => {
  return await authFetch(`/tickets/user/${userId}`);
};

// Get user orders
export const getUserOrders = async (userId: string) => {
  try {
    return await authFetch(`/orders/user/${userId}`);
  } catch (error) {
    console.error('Get user orders error:', error);
    throw error;
  }
};

// Initiate M-Pesa payment
export const initiateMpesaPayment = async (
  phoneNumber: string,
  amount: number,
  orderType: 'artwork' | 'exhibition',
  orderId: string,
  userId: string,
  accountReference: string
) => {
  try {
    const response = await fetch(`${API_URL}/mpesa/stk-push`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        phoneNumber,
        amount,
        orderType,
        orderId,
        userId,
        accountReference
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Payment initiation failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('M-Pesa payment error:', error);
    throw error;
  }
};

// Check M-Pesa transaction status
export const checkPaymentStatus = async (checkoutRequestId: string) => {
  try {
    const response = await fetch(`${API_URL}/mpesa/status/${checkoutRequestId}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to check payment status');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Payment status check error:', error);
    throw error;
  }
};
