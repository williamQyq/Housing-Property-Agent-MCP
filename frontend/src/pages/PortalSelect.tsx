import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, UserCheck, Home } from "lucide-react";
import heroProperty from "@/assets/hero-property.jpg";

const PortalSelect = () => {
  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Header */}
      <header className="bg-background/80 backdrop-blur-sm border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-2">
            <Home className="h-8 w-8 text-primary" />
            <h1 className="text-2xl font-bold text-foreground">PropertyHub</h1>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-5xl font-bold text-foreground mb-6 leading-tight">
                Streamline Your <span className="bg-gradient-primary bg-clip-text text-transparent">Property Management</span>
              </h1>
              <p className="text-xl text-muted-foreground mb-8 leading-relaxed">
                Connect landlords and tenants with modern tools for maintenance requests, communication, and seamless property management.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <Button variant="hero" size="lg" className="text-lg">
                  Get Started Today
                </Button>
                <Button variant="outline" size="lg" className="text-lg">
                  Learn More
                </Button>
              </div>
            </div>
            <div className="relative">
              <img 
                src={heroProperty} 
                alt="Modern apartment building" 
                className="rounded-2xl shadow-elevated w-full h-auto"
              />
              <div className="absolute inset-0 bg-gradient-primary opacity-10 rounded-2xl"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Portal Selection */}
      <section className="py-16 px-4">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-foreground mb-4">Choose Your Portal</h2>
            <p className="text-lg text-muted-foreground">Access the tools designed specifically for your role</p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            {/* Tenant Portal */}
            <Card className="group hover:shadow-glow transition-all duration-300 border-2 hover:border-primary/20">
              <CardHeader className="text-center pb-4">
                <div className="mx-auto mb-4 p-4 bg-gradient-warm rounded-full w-fit">
                  <UserCheck className="h-12 w-12 text-primary" />
                </div>
                <CardTitle className="text-2xl">Tenant Portal</CardTitle>
                <CardDescription className="text-base">
                  Submit maintenance requests, track progress, and communicate with your landlord effortlessly.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-primary rounded-full"></div>
                    Chat-style maintenance requests
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-primary rounded-full"></div>
                    Photo uploads and descriptions
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-primary rounded-full"></div>
                    Real-time status updates
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-primary rounded-full"></div>
                    Landlord notifications and notices
                  </li>
                </ul>
                <Link to="/tenant" className="block">
                  <Button variant="portal" className="w-full mt-6 text-lg py-6">
                    Access Tenant Portal
                  </Button>
                </Link>
              </CardContent>
            </Card>

            {/* Landlord Portal */}
            <Card className="group hover:shadow-glow transition-all duration-300 border-2 hover:border-primary/20">
              <CardHeader className="text-center pb-4">
                <div className="mx-auto mb-4 p-4 bg-gradient-warm rounded-full w-fit">
                  <Building2 className="h-12 w-12 text-primary" />
                </div>
                <CardTitle className="text-2xl">Landlord Portal</CardTitle>
                <CardDescription className="text-base">
                  Manage properties, track maintenance requests, and generate lease contracts with ease.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-primary rounded-full"></div>
                    Request management dashboard
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-primary rounded-full"></div>
                    Tenant candidate management
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-primary rounded-full"></div>
                    Automated lease generation
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-primary rounded-full"></div>
                    Workflow management tools
                  </li>
                </ul>
                <Link to="/landlord" className="block">
                  <Button variant="portal" className="w-full mt-6 text-lg py-6">
                    Access Landlord Portal
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-muted/50 py-12 px-4 mt-20">
        <div className="container mx-auto max-w-4xl text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Home className="h-6 w-6 text-primary" />
            <span className="text-lg font-semibold">PropertyHub</span>
          </div>
          <p className="text-muted-foreground">
            Revolutionizing property management, one connection at a time.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default PortalSelect;