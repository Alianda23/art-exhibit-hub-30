
import { Artwork } from '@/types';
import { authFetch } from '@/services/api';

interface UserPreferences {
  favoriteArtists: string[];
  preferredMediums: string[];
  priceRanges: { min: number; max: number }[];
  purchaseHistory: {
    artworkId: string;
    artist: string;
    medium: string;
    price: number;
  }[];
  exhibitionHistory: {
    exhibitionId: string;
    exhibitionTitle: string;
  }[];
}

export class RecommendationEngine {
  
  // Generate recommendations based on user's purchase and exhibition history
  static async generatePersonalizedRecommendations(
    userId: string, 
    allArtworks: Artwork[], 
    maxRecommendations: number = 6
  ): Promise<Artwork[]> {
    try {
      console.log('Generating personalized recommendations for user:', userId);
      
      // Fetch user's order and booking history
      const userHistory = await authFetch(`/user/${userId}/orders`);
      
      if (!userHistory || userHistory.error) {
        console.log('No user history found, user needs to make first purchase');
        return []; // Return empty array for users with no history
      }
      
      // Check if user has any actual purchases
      const hasPurchases = userHistory.orders && userHistory.orders.length > 0;
      
      if (!hasPurchases) {
        console.log('User has no purchase history, returning empty recommendations');
        return []; // Return empty array if no purchases
      }
      
      const preferences = this.analyzeUserPreferences(userHistory);
      console.log('User preferences analyzed:', preferences);
      
      // Get list of artwork IDs the user has already purchased
      const purchasedArtworkIds = preferences.purchaseHistory.map(p => p.artworkId);
      console.log('User has purchased these artworks:', purchasedArtworkIds);
      
      // Filter out artworks the user has already purchased
      const availableArtworks = allArtworks.filter(artwork => 
        artwork.status === 'available' && 
        !purchasedArtworkIds.includes(artwork.id.toString()) &&
        !purchasedArtworkIds.includes(artwork.id)
      );
      
      console.log(`Filtered artworks: ${availableArtworks.length} available (excluding ${purchasedArtworkIds.length} already purchased)`);
      
      if (availableArtworks.length === 0) {
        console.log('No available artworks left after filtering purchased items');
        return [];
      }
      
      // Score all available artworks based on user preferences
      const scoredArtworks = availableArtworks
        .map(artwork => ({
          artwork,
          score: this.calculateRecommendationScore(artwork, preferences)
        }))
        .sort((a, b) => b.score - a.score);
      
      console.log('Top scored artworks:', scoredArtworks.slice(0, 3).map(s => ({ 
        title: s.artwork.title, 
        artist: s.artwork.artist,
        score: s.score 
      })));
      
      return scoredArtworks
        .slice(0, maxRecommendations)
        .map(item => item.artwork);
        
    } catch (error) {
      console.error('Error generating personalized recommendations:', error);
      return []; // Return empty array on error for personalized recommendations
    }
  }
  
  // Analyze user's past behavior to understand preferences
  private static analyzeUserPreferences(userHistory: any): UserPreferences {
    const preferences: UserPreferences = {
      favoriteArtists: [],
      preferredMediums: [],
      priceRanges: [],
      purchaseHistory: [],
      exhibitionHistory: []
    };
    
    // Analyze artwork orders
    if (userHistory.orders && userHistory.orders.length > 0) {
      const artistCount: { [key: string]: number } = {};
      const mediumCount: { [key: string]: number } = {};
      const prices: number[] = [];
      
      userHistory.orders.forEach((order: any) => {
        // Count artist preferences
        artistCount[order.artist] = (artistCount[order.artist] || 0) + 1;
        
        // Count medium preferences (if available)
        if (order.medium) {
          mediumCount[order.medium] = (mediumCount[order.medium] || 0) + 1;
        }
        
        // Collect price data
        prices.push(order.price || order.totalAmount);
        
        // Store purchase history with proper artwork ID handling
        preferences.purchaseHistory.push({
          artworkId: order.artworkId || order.artwork_id,
          artist: order.artist,
          medium: order.medium || 'Unknown',
          price: order.price || order.totalAmount
        });
      });
      
      // Determine favorite artists (those with multiple purchases or high frequency)
      preferences.favoriteArtists = Object.entries(artistCount)
        .filter(([_, count]) => count > 0)
        .sort(([_, a], [__, b]) => b - a)
        .map(([artist, _]) => artist);
      
      // Determine preferred mediums
      preferences.preferredMediums = Object.entries(mediumCount)
        .sort(([_, a], [__, b]) => b - a)
        .map(([medium, _]) => medium);
      
      // Determine price ranges based on past purchases
      if (prices.length > 0) {
        const avgPrice = prices.reduce((sum, price) => sum + price, 0) / prices.length;
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        
        preferences.priceRanges.push({
          min: Math.max(0, avgPrice * 0.5), // 50% below average
          max: avgPrice * 2 // 100% above average
        });
        
        // Add the actual range they've purchased in
        preferences.priceRanges.push({
          min: minPrice * 0.8,
          max: maxPrice * 1.2
        });
      }
    }
    
    // Analyze exhibition bookings for additional insights
    if (userHistory.bookings && userHistory.bookings.length > 0) {
      userHistory.bookings.forEach((booking: any) => {
        preferences.exhibitionHistory.push({
          exhibitionId: booking.exhibitionId,
          exhibitionTitle: booking.exhibitionTitle
        });
      });
    }
    
    return preferences;
  }
  
  // Calculate recommendation score for an artwork based on user preferences
  private static calculateRecommendationScore(artwork: Artwork, preferences: UserPreferences): number {
    let score = 0;
    
    // Artist preference scoring (highest weight)
    if (preferences.favoriteArtists.includes(artwork.artist)) {
      const artistIndex = preferences.favoriteArtists.indexOf(artwork.artist);
      score += 100 - (artistIndex * 20); // First favorite gets 100, second gets 80, etc.
    }
    
    // Medium preference scoring
    if (preferences.preferredMediums.includes(artwork.medium)) {
      const mediumIndex = preferences.preferredMediums.indexOf(artwork.medium);
      score += 40 - (mediumIndex * 10); // First preferred medium gets 40, second gets 30, etc.
    }
    
    // Price range scoring
    const artworkPrice = artwork.price;
    const inPriceRange = preferences.priceRanges.some(range => 
      artworkPrice >= range.min && artworkPrice <= range.max
    );
    if (inPriceRange) {
      score += 30;
    }
    
    // Similar artist bonus (artists with similar styles to purchased ones)
    const similarArtistBonus = preferences.favoriteArtists.some(favoriteArtist => {
      // Check if this artwork is by a different artist but similar style
      return artwork.artist !== favoriteArtist && 
             artwork.artist.toLowerCase().includes(favoriteArtist.toLowerCase().split(' ')[0]);
    });
    if (similarArtistBonus) {
      score += 15;
    }
    
    // Add small randomness to avoid always showing the same order
    score += Math.random() * 5;
    
    return score;
  }
  
  // Fallback recommendations when no user history is available
  private static generateGeneralRecommendations(allArtworks: Artwork[], maxRecommendations: number): Artwork[] {
    console.log('Generating general recommendations');
    
    const availableArtworks = allArtworks.filter(artwork => artwork.status === 'available');
    
    // Simple randomization with some preference for medium-priced items
    const shuffled = availableArtworks
      .sort(() => 0.5 - Math.random())
      .slice(0, maxRecommendations);
    
    return shuffled;
  }
  
  // Get recommendations for similar artworks (for artwork detail pages)
  static generateSimilarArtworkRecommendations(
    currentArtwork: Artwork, 
    allArtworks: Artwork[], 
    maxRecommendations: number = 4
  ): Artwork[] {
    return allArtworks
      .filter(artwork => 
        artwork.id !== currentArtwork.id && 
        artwork.status === 'available' &&
        (artwork.artist === currentArtwork.artist || 
         artwork.medium === currentArtwork.medium ||
         Math.abs(artwork.price - currentArtwork.price) < currentArtwork.price * 0.5)
      )
      .sort(() => 0.5 - Math.random())
      .slice(0, maxRecommendations);
  }
}
