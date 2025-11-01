import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

const TenantPortal = () => {
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
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold">
            Welcome to the New Tenant Portal
          </h2>
          <p className="text-muted-foreground">
            This portal is being updated to use the new ai-sdk-ui architecture
            with phone authentication and room management.
          </p>
          <p className="text-sm text-muted-foreground">
            The new system will include phone-based OTP authentication and room
            setup tools.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TenantPortal;
