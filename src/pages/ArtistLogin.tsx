
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { loginArtist, isArtist } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Loader2 } from 'lucide-react';
import TwoFactorVerification from '@/components/TwoFactorVerification';

const ArtistLogin = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showTwoFactor, setShowTwoFactor] = useState(false);
  const [pendingCredentials, setPendingCredentials] = useState<{email: string, password: string} | null>(null);
  const { toast } = useToast();
  const navigate = useNavigate();
  
  // Redirect if already logged in as artist
  React.useEffect(() => {
    if (isArtist()) {
      navigate('/artist');
    }
  }, [navigate]);

  const sendTwoFactorCode = async (userEmail: string, userType: 'user' | 'artist' = 'artist') => {
    try {
      const response = await fetch('http://localhost:8000/send-2fa-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userEmail,
          userType
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to send verification code');
      }
      
      return data;
    } catch (error) {
      console.error('Error sending 2FA code:', error);
      throw error;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast({
        title: "Error",
        description: "Email and password are required.",
        variant: "destructive"
      });
      return;
    }
    
    setLoading(true);
    
    try {
      // First, validate credentials without logging in
      const response = await fetch('http://localhost:8000/validate-credentials', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          userType: 'artist'
        }),
      });

      const data = await response.json();
      
      if (data.valid) {
        // Credentials are valid, send 2FA code
        await sendTwoFactorCode(email, 'artist');
        setPendingCredentials({ email, password });
        setShowTwoFactor(true);
        
        toast({
          title: "Verification Code Sent",
          description: "Please check your email for the verification code.",
        });
      } else {
        toast({
          title: "Login Failed",
          description: data.error || "Invalid email or password",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "An error occurred. Please try again.",
        variant: "destructive"
      });
      console.error("Login error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleTwoFactorSuccess = async () => {
    if (!pendingCredentials) return;
    
    try {
      const response = await loginArtist(pendingCredentials);
      
      if (response.error) {
        toast({
          title: "Login Failed",
          description: response.error,
          variant: "destructive"
        });
      } else {
        toast({
          title: "Success",
          description: "Login successful. Welcome to your artist portal!",
        });
        navigate('/artist');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Login failed after verification. Please try again.",
        variant: "destructive"
      });
      setShowTwoFactor(false);
      setPendingCredentials(null);
    }
  };

  const handleResendCode = async () => {
    if (!pendingCredentials) return;
    await sendTwoFactorCode(pendingCredentials.email, 'artist');
  };

  if (showTwoFactor && pendingCredentials) {
    return (
      <TwoFactorVerification
        email={pendingCredentials.email}
        userType="artist"
        onVerificationSuccess={handleTwoFactorSuccess}
        onResendCode={handleResendCode}
      />
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-3xl font-bold">Artist Login</CardTitle>
          <CardDescription>
            Enter your credentials to access your artist portal
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="artist@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link to="/forgot-password" className="text-sm text-blue-500 hover:text-blue-700">
                  Forgot password?
                </Link>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Validating...
                </>
              ) : (
                "Login"
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <div className="text-sm text-center text-gray-500">
            Don't have an artist account?{" "}
            <Link to="/artist-signup" className="text-blue-500 hover:text-blue-700">
              Sign up
            </Link>
          </div>
          <div className="text-sm text-center text-gray-500">
            <Link to="/login" className="text-blue-500 hover:text-blue-700">
              User Login
            </Link>
            {" | "}
            <Link to="/admin-login" className="text-blue-500 hover:text-blue-700">
              Admin Login
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
};

export default ArtistLogin;
