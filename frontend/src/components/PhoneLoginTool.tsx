import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Phone, CheckCircle, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface PhoneLoginToolProps {
  onAuthSuccess: (userData: any) => void;
}

export const PhoneLoginTool = ({ onAuthSuccess }: PhoneLoginToolProps) => {
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"phone" | "code">("phone");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const normalizePhone = (phone: string) => {
    // Remove all non-digit characters
    const digits = phone.replace(/\D/g, "");

    // Handle different formats
    if (digits.length === 10) {
      return `+1${digits}`;
    } else if (digits.length === 11 && digits[0] === "1") {
      return `+${digits}`;
    } else if (digits.length > 11) {
      return `+${digits}`;
    }

    return phone;
  };

  const handleStartOTP = async () => {
    if (!phone.trim()) {
      toast({
        title: "Phone Required",
        description: "Please enter your phone number",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const normalizedPhone = normalizePhone(phone);

      // Call BFF service
      const response = await fetch("/api/v1/auth/otp/start", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ phone: normalizedPhone }),
      });

      const data = await response.json();

      if (data.success) {
        setStep("code");
        toast({
          title: "Code Sent",
          description: `Verification code sent to ${normalizedPhone}`,
        });
      } else {
        toast({
          title: "Error",
          description: data.message || "Failed to send code",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send verification code",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!code.trim()) {
      toast({
        title: "Code Required",
        description: "Please enter the verification code",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const normalizedPhone = normalizePhone(phone);

      // Call BFF service
      const response = await fetch("/api/v1/auth/otp/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          phone: normalizedPhone,
          code: code,
        }),
      });

      const data = await response.json();

      if (data.success && data.user_id) {
        // Store token in localStorage
        if (data.token) {
          localStorage.setItem("auth_token", data.token);
        }

        toast({
          title: "Success",
          description: "Phone verified successfully!",
        });

        onAuthSuccess({
          user_id: data.user_id,
          phone: normalizedPhone,
        });
      } else {
        toast({
          title: "Verification Failed",
          description: data.message || "Invalid verification code",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to verify code",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleBackToPhone = () => {
    setStep("phone");
    setCode("");
  };

  return (
    <div className="space-y-4">
      {step === "phone" && (
        <>
          <div className="space-y-2">
            <Label htmlFor="phone">Phone Number</Label>
            <Input
              id="phone"
              type="tel"
              placeholder="+1 (555) 123-4567"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="text-center text-lg"
            />
            <p className="text-xs text-muted-foreground text-center">
              Enter your phone number to receive a verification code
            </p>
          </div>

          <Button
            onClick={handleStartOTP}
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Sending Code...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4" />
                Send Verification Code
              </div>
            )}
          </Button>
        </>
      )}

      {step === "code" && (
        <>
          <div className="space-y-2">
            <Label htmlFor="code">Verification Code</Label>
            <Input
              id="code"
              type="text"
              placeholder="123456"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="text-center text-lg tracking-widest"
              maxLength={6}
            />
            <p className="text-xs text-muted-foreground text-center">
              Enter the 6-digit code sent to {normalizePhone(phone)}
            </p>
          </div>

          <div className="space-y-2">
            <Button
              onClick={handleVerifyOTP}
              disabled={loading}
              className="w-full"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Verifying...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4" />
                  Verify Code
                </div>
              )}
            </Button>

            <Button
              onClick={handleBackToPhone}
              variant="outline"
              className="w-full"
            >
              Back to Phone Number
            </Button>
          </div>
        </>
      )}
    </div>
  );
};
