import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, UserPlus, CheckCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface RoomSetupToolProps {
  onRoomCreated: (roomData: any) => void;
  userProfile: { user_id?: string; rooms: any[] };
}

export const RoomSetupTool = ({
  onRoomCreated,
  userProfile,
}: RoomSetupToolProps) => {
  const [roomName, setRoomName] = useState("");
  const [role, setRole] = useState<"LANDLORD" | "TENANT">("TENANT");
  const [invitePhone, setInvitePhone] = useState("");
  const [inviteRole, setInviteRole] = useState<"LANDLORD" | "TENANT">(
    "LANDLORD"
  );
  const [step, setStep] = useState<"create" | "invite">("create");
  const [loading, setLoading] = useState(false);
  const [createdRoom, setCreatedRoom] = useState<any>(null);
  const { toast } = useToast();

  const normalizePhone = (phone: string) => {
    const digits = phone.replace(/\D/g, "");
    if (digits.length === 10) {
      return `+1${digits}`;
    } else if (digits.length === 11 && digits[0] === "1") {
      return `+${digits}`;
    } else if (digits.length > 11) {
      return `+${digits}`;
    }
    return phone;
  };

  const handleCreateRoom = async () => {
    if (!roomName.trim()) {
      toast({
        title: "Room Name Required",
        description: "Please enter a room name",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem("auth_token");

      const response = await fetch("/api/v1/rooms", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: roomName,
          role: role,
        }),
      });

      const data = await response.json();

      if (data.success) {
        const roomData = {
          id: data.room_id,
          name: roomName,
          role: role,
          created_at: new Date().toISOString(),
        };

        setCreatedRoom(roomData);
        setStep("invite");

        toast({
          title: "Room Created",
          description: `Room "${roomName}" created successfully!`,
        });
      } else {
        toast({
          title: "Error",
          description: data.message || "Failed to create room",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create room",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSendInvite = async () => {
    if (!invitePhone.trim()) {
      toast({
        title: "Phone Required",
        description: "Please enter the invitee's phone number",
        variant: "destructive",
      });
      return;
    }

    if (!createdRoom) {
      toast({
        title: "No Room",
        description: "Please create a room first",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem("auth_token");
      const normalizedPhone = normalizePhone(invitePhone);

      const response = await fetch(`/api/v1/rooms/${createdRoom.id}/invites`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          phone: normalizedPhone,
          role: inviteRole,
        }),
      });

      const data = await response.json();

      if (data.success) {
        toast({
          title: "Invite Sent",
          description: `Invitation sent to ${normalizedPhone}`,
        });

        onRoomCreated(createdRoom);
      } else {
        toast({
          title: "Error",
          description: data.message || "Failed to send invite",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send invite",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSkipInvite = () => {
    onRoomCreated(createdRoom);
  };

  return (
    <div className="space-y-6">
      {step === "create" && (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="roomName">Room Name</Label>
            <Input
              id="roomName"
              placeholder="e.g., Main Apartment, House 123"
              value={roomName}
              onChange={(e) => setRoomName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="role">Your Role</Label>
            <Select
              value={role}
              onValueChange={(value: "LANDLORD" | "TENANT") => setRole(value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="TENANT">Tenant</SelectItem>
                <SelectItem value="LANDLORD">Landlord</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button
            onClick={handleCreateRoom}
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Creating Room...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                Create Room
              </div>
            )}
          </Button>
        </div>
      )}

      {step === "invite" && createdRoom && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-600">
                <CheckCircle className="h-5 w-5" />
                Room Created Successfully
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Room: <strong>{createdRoom.name}</strong>
                <br />
                Your Role: <strong>{createdRoom.role}</strong>
              </p>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Invite the Other Party</h3>

            <div className="space-y-2">
              <Label htmlFor="invitePhone">Phone Number</Label>
              <Input
                id="invitePhone"
                type="tel"
                placeholder="+1 (555) 123-4567"
                value={invitePhone}
                onChange={(e) => setInvitePhone(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="inviteRole">Their Role</Label>
              <Select
                value={inviteRole}
                onValueChange={(value: "LANDLORD" | "TENANT") =>
                  setInviteRole(value)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="LANDLORD">Landlord</SelectItem>
                  <SelectItem value="TENANT">Tenant</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Button
                onClick={handleSendInvite}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Sending Invite...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <UserPlus className="h-4 w-4" />
                    Send Invite
                  </div>
                )}
              </Button>

              <Button
                onClick={handleSkipInvite}
                variant="outline"
                className="w-full"
              >
                Skip for Now
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
