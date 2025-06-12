import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { isAdmin, getAllTickets, generateExhibitionTicket } from '@/services/api';
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import { format } from 'date-fns';
import { createImageSrc, handleImageError, preloadImage } from '@/utils/imageUtils';

interface Ticket {
  id: string;
  user_id: string;
  user_name: string;
  exhibition_id: string;
  exhibition_title: string;
  exhibition_image_url?: string;
  booking_date: string;
  ticket_code: string;
  slots: number;
  status: 'active' | 'used' | 'cancelled';
  total_amount: number;
  payment_status: 'pending' | 'completed' | 'failed';
}

const AdminTickets = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [generatingTicket, setGeneratingTicket] = useState<string | null>(null);

  useEffect(() => {
    if (!isAdmin()) {
      navigate('/admin-login');
      return;
    }
    
    console.log("Admin tickets page loaded, user is admin");
  }, [navigate]);

  const { data, isLoading, error } = useQuery({
    queryKey: ['tickets'],
    queryFn: getAllTickets,
  });

  // Log tickets data and preload images when data is available
  useEffect(() => {
    console.log("Tickets data:", data);
    if (error) {
      console.error("Error fetching tickets:", error);
    }
    
    // Preload all ticket images when data is available
    if (data?.tickets) {
      data.tickets.forEach((ticket: Ticket) => {
        if (ticket.exhibition_image_url) {
          preloadImage(ticket.exhibition_image_url);
        }
      });
    }
  }, [data, error]);

  const handlePrintTicket = async (bookingId: string) => {
    try {
      setGeneratingTicket(bookingId);
      console.log(`Generating ticket for booking: ${bookingId}`);
      
      const response = await generateExhibitionTicket(bookingId);
      console.log("Ticket generation response:", response);
      
      // Check for different possible response formats
      if (response) {
        let pdfData = null;
        
        // Handle different response formats
        if (response.pdfData) {
          pdfData = response.pdfData;
        } else if (response.pdf) {
          pdfData = response.pdf;
        } else if (response.data) {
          pdfData = response.data;
        } else if (typeof response === 'string') {
          // Response might be base64 string directly
          pdfData = response;
        }
        
        if (pdfData) {
          try {
            // Try to create blob from different data formats
            let blob;
            
            if (typeof pdfData === 'string') {
              // Assume it's base64 encoded
              const binaryString = atob(pdfData);
              const bytes = new Uint8Array(binaryString.length);
              for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
              }
              blob = new Blob([bytes], { type: 'application/pdf' });
            } else {
              // Assume it's already binary data
              blob = new Blob([pdfData], { type: 'application/pdf' });
            }
            
            const pdfUrl = URL.createObjectURL(blob);
            console.log('Created PDF URL:', pdfUrl);
            
            // Open in new window
            const newWindow = window.open(pdfUrl, '_blank');
            if (!newWindow) {
              // If popup was blocked, try download instead
              const link = document.createElement('a');
              link.href = pdfUrl;
              link.download = `ticket-${bookingId}.pdf`;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
            }
            
            // Clean up the URL after a delay
            setTimeout(() => {
              URL.revokeObjectURL(pdfUrl);
            }, 1000);
            
            toast({
              title: "Success",
              description: "Ticket generated and opened successfully",
            });
          } catch (blobError) {
            console.error("Error creating PDF blob:", blobError);
            toast({
              title: "Error",
              description: "Failed to process PDF data",
              variant: "destructive",
            });
          }
        } else {
          console.error("No PDF data found in response:", response);
          toast({
            title: "Error",
            description: "No PDF data received from server",
            variant: "destructive",
          });
        }
      } else {
        console.error("Empty response from server");
        toast({
          title: "Error",
          description: "Empty response from server",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error generating ticket:", error);
      toast({
        title: "Error",
        description: `Failed to generate ticket: ${error instanceof Error ? error.message : 'Unknown error'}`,
        variant: "destructive",
      });
    } finally {
      setGeneratingTicket(null);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'PPP p');
    } catch (error) {
      console.error(`Error formatting date: ${dateString}`, error);
      return dateString;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'used':
        return 'bg-yellow-500';
      case 'cancelled':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-2xl font-bold mb-6">Exhibition Tickets</h1>
        <div className="flex justify-center items-center h-64">
          <p className="text-lg">Loading tickets...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-2xl font-bold mb-6">Exhibition Tickets</h1>
        <div className="flex justify-center items-center h-64">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <p className="font-bold">Error loading tickets</p>
            <p>{(error as Error).message || "Unknown error occurred"}</p>
          </div>
        </div>
      </div>
    );
  }

  const tickets = data?.tickets || [];

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Exhibition Tickets</h1>
      
      <div className="grid gap-6 md:grid-cols-[1fr_1fr]">
        <Card className="p-4">
          <h2 className="text-xl font-semibold mb-4">All Tickets ({tickets.length})</h2>
          
          {tickets.length === 0 ? (
            <p className="text-gray-500 p-4 text-center">No tickets to display</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Exhibition</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tickets.map((ticket: Ticket) => (
                    <TableRow key={ticket.id}>
                      <TableCell>{ticket.user_name}</TableCell>
                      <TableCell>{ticket.exhibition_title}</TableCell>
                      <TableCell>{format(new Date(ticket.booking_date), 'PPP p')}</TableCell>
                      <TableCell>
                        <Badge className={ticket.status === 'active' ? 'bg-green-500' : ticket.status === 'used' ? 'bg-yellow-500' : 'bg-red-500'}>
                          {ticket.status.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => setSelectedTicket(ticket)}
                          >
                            View
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm"
                            className="bg-blue-50 text-blue-600 hover:bg-blue-100"
                            onClick={() => handlePrintTicket(ticket.id)}
                            disabled={generatingTicket === ticket.id}
                          >
                            {generatingTicket === ticket.id ? 'Generating...' : 'Print'}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </Card>
        
        <Card className="p-4">
          {selectedTicket ? (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Ticket Details</h2>
                <Button 
                  size="sm" 
                  variant="outline"
                  className="bg-blue-50 text-blue-600 hover:bg-blue-100"
                  onClick={() => handlePrintTicket(selectedTicket.id)}
                  disabled={generatingTicket === selectedTicket.id}
                >
                  {generatingTicket === selectedTicket.id ? 'Generating...' : 'Print Ticket'}
                </Button>
              </div>
              
              <div className="space-y-4">
                {selectedTicket.exhibition_image_url && (
                  <div className="mb-4">
                    <img 
                      src={createImageSrc(selectedTicket.exhibition_image_url)} 
                      alt={selectedTicket.exhibition_title} 
                      className="w-full h-48 object-cover rounded-md"
                      onError={(e) => {
                        console.error(`Failed to load image: ${selectedTicket.exhibition_image_url}`);
                        (e.target as HTMLImageElement).src = "/placeholder.svg";
                      }}
                    />
                  </div>
                )}
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <p className="text-sm text-gray-500">User:</p>
                    <p className="font-medium">{selectedTicket.user_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Exhibition:</p>
                    <p className="font-medium">{selectedTicket.exhibition_title}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Booking Date:</p>
                    <p>{format(new Date(selectedTicket.booking_date), 'PPP p')}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Slots:</p>
                    <p>{selectedTicket.slots}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Ticket Code:</p>
                    <p className="font-mono bg-gray-100 px-2 py-1 rounded">{selectedTicket.ticket_code}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Status:</p>
                    <Badge className={selectedTicket.status === 'active' ? 'bg-green-500' : selectedTicket.status === 'used' ? 'bg-yellow-500' : 'bg-red-500'}>
                      {selectedTicket.status.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64">
              <p className="text-gray-500">Select a ticket to view details</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default AdminTickets;
