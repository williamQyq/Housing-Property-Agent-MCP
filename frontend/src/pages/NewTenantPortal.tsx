import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Phone, Users, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PhoneLoginTool } from "@/components/PhoneLoginTool";
import { RoomSetupTool } from "@/components/RoomSetupTool";
import { ChatInterface } from "@/components/ChatInterface";

const NewTenantPortal = () => {
  const [authState, setAuthState] = useState<"ANON" | "AUTHENTICATED">("ANON");
  const [userProfile, setUserProfile] = useState<{
    user_id?: string;
    rooms: any[];
  }>({ rooms: [] });
  const [currentStep, setCurrentStep] = useState<
    "login" | "room-setup" | "chat"
  >("login");

  const handleAuthSuccess = (userData: any) => {
    setAuthState("AUTHENTICATED");
    setUserProfile({ user_id: userData.user_id, rooms: [] });
    setCurrentStep("room-setup");
  };

  const handleRoomCreated = (roomData: any) => {
    setUserProfile((prev) => ({
      ...prev,
      rooms: [...prev.rooms, roomData],
    }));
    setCurrentStep("chat");
  };

  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Header */}
      <header className="bg-background/80 backdrop-blur-sm border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link
              to="/"
              className="flex items-center gap-2 text-primary hover:text-primary/80 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
              Back to Portals
            </Link>
            <h1 className="text-xl font-semibold text-foreground">
              Tenant Portal
            </h1>
            {authState === "AUTHENTICATED" && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Phone className="h-4 w-4" />
                User ID: {userProfile.user_id?.slice(0, 8)}...
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {currentStep === "login" && (
          <div className="space-y-6">
            <div className="text-center space-y-4">
              <h2 className="text-3xl font-bold">Welcome to Housing Portal</h2>
              <p className="text-muted-foreground">
                Get started by logging in with your phone number
              </p>
            </div>

            <Card className="max-w-md mx-auto">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Phone className="h-5 w-5 text-primary" />
                  Phone Authentication
                </CardTitle>
                <CardDescription>
                  Enter your phone number to receive a verification code
                </CardDescription>
              </CardHeader>
              <CardContent>
                <PhoneLoginTool onAuthSuccess={handleAuthSuccess} />
              </CardContent>
            </Card>
          </div>
        )}

        {currentStep === "room-setup" && (
          <div className="space-y-6">
            <div className="text-center space-y-4">
              <h2 className="text-3xl font-bold">Set Up Your Room</h2>
              <p className="text-muted-foreground">
                Create a room and invite your landlord or tenant
              </p>
            </div>

            <Card className="max-w-md mx-auto">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-primary" />
                  Room Setup
                </CardTitle>
                <CardDescription>
                  Create a room and select your role
                </CardDescription>
              </CardHeader>
              <CardContent>
                <RoomSetupTool
                  onRoomCreated={handleRoomCreated}
                  userProfile={userProfile}
                />
              </CardContent>
            </Card>
          </div>
        )}

        {currentStep === "chat" && (
          <div className="space-y-6">
            <div className="text-center space-y-4">
              <h2 className="text-3xl font-bold">Housing Assistant</h2>
              <p className="text-muted-foreground">
                Your AI-powered housing assistant is ready to help
              </p>
            </div>

            <Card className="max-w-4xl mx-auto">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5 text-primary" />
                  Chat Interface
                </CardTitle>
                <CardDescription>
                  Ask questions, create maintenance requests, or manage your
                  housing needs
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ChatInterface
                  userProfile={userProfile}
                  authState={authState}
                />
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default NewTenantPortal;
