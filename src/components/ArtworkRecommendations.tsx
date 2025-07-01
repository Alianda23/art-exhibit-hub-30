
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, User, ShoppingCart } from 'lucide-react';
import { Button } from '@/components/ui/button';
import ArtworkCard from '@/components/ArtworkCard';
import { getAllArtworks } from '@/services/api';
import { Artwork } from '@/types';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { RecommendationEngine } from '@/services/recommendationService';

const ArtworkRecommendations = () => {
  const [recommendedArtworks, setRecommendedArtworks] = useState<Artwork[]>([]);
  const [loading, setLoading] = useState(true);
  const [isPersonalized, setIsPersonalized] = useState(false);
  const [userHasNoPurchases, setUserHasNoPurchases] = useState(false);
  const { toast } = useToast();
  const { currentUser, isAuthenticated } = useAuth();

  useEffect(() => {
    const fetchAndGenerateRecommendations = async () => {
      try {
        setLoading(true);
        const allArtworks = await getAllArtworks();
        console.log("Fetched artworks for recommendations:", allArtworks.length);
        
        let recommendations: Artwork[] = [];
        let personalized = false;
        let noPurchases = false;
        
        // Generate personalized recommendations if user is authenticated
        if (isAuthenticated && currentUser?.id) {
          console.log("Generating personalized recommendations for user:", currentUser.id);
          recommendations = await RecommendationEngine.generatePersonalizedRecommendations(
            currentUser.id, 
            allArtworks, 
            3
          );
          
          if (recommendations.length === 0) {
            console.log("No personalized recommendations - user has no purchase history");
            noPurchases = true;
          } else {
            personalized = true;
          }
        }
        
        // Fallback to general recommendations only for non-authenticated users
        if (!isAuthenticated && recommendations.length === 0) {
          console.log("Generating general recommendations for non-authenticated user");
          recommendations = RecommendationEngine.generateSimilarArtworkRecommendations(
            allArtworks[0] || {} as Artwork, 
            allArtworks, 
            3
          );
        }
        
        setRecommendedArtworks(recommendations);
        setIsPersonalized(personalized);
        setUserHasNoPurchases(noPurchases);
      } catch (error) {
        console.error('Failed to fetch artwork recommendations:', error);
        toast({
          title: "Error",
          description: "Failed to load artwork recommendations. Please try again later.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };
    
    fetchAndGenerateRecommendations();
  }, [toast, isAuthenticated, currentUser]);

  // Don't show the section if authenticated user has no purchases
  if (isAuthenticated && userHasNoPurchases) {
    return null;
  }

  return (
    <section className="py-20 bg-secondary">
      <div className="container mx-auto px-4 md:px-6">
        <div className="flex justify-between items-center mb-12">
          <div className="flex items-center gap-2">
            {isPersonalized ? (
              <User className="h-6 w-6 text-gold" />
            ) : (
              <Sparkles className="h-6 w-6 text-gold" />
            )}
            <h2 className="text-3xl md:text-4xl font-serif font-bold">
              {isPersonalized ? (
                <>Recommended <span className="text-gold">For You</span></>
              ) : (
                <>Featured <span className="text-gold">Recommendations</span></>
              )}
            </h2>
          </div>
          <Link to="/artworks">
            <Button variant="ghost" className="text-gold hover:text-gold-dark flex items-center gap-2">
              View All <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
        
        {isPersonalized && (
          <div className="mb-8 p-4 bg-gold/10 rounded-lg border border-gold/20">
            <p className="text-sm text-gray-700">
              <strong>Personalized for you:</strong> These recommendations are based on your purchase history and preferences.
            </p>
          </div>
        )}
        
        <div className="artwork-grid">
          {loading ? (
            <p className="text-center w-full">Loading recommendations...</p>
          ) : recommendedArtworks.length > 0 ? (
            recommendedArtworks.map((artwork) => (
              <ArtworkCard key={artwork.id} artwork={artwork} />
            ))
          ) : (
            <div className="text-center w-full">
              <p className="mb-4">No recommendations found. Please check back later.</p>
              {!isAuthenticated && (
                <p className="text-sm text-gray-600">
                  <Link to="/login" className="text-gold hover:text-gold-dark underline">
                    Sign in
                  </Link> to get personalized recommendations based on your preferences.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default ArtworkRecommendations;
