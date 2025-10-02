import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Chat } from "@/components/ui/chat";
import { AnimatedList } from "@/components/ui/animated-list";
import { ArrowLeft, Send, Upload, Clock, CheckCircle, AlertTriangle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useWorkflows, type WorkflowEntry, type WorkflowStep } from "@/hooks/useWorkflows";

interface MaintenanceRequest {
  id: string;
  description: string;
  urgency: "low" | "medium" | "high" | "urgent";
  category: string;
  status: "open" | "in-progress" | "resolved";
  date: string;
  image?: string;
}

const TenantPortal = () => {
  const { toast } = useToast();
  const [description, setDescription] = useState("");
  const [urgency, setUrgency] = useState("");
  const [category, setCategory] = useState("");
  // Two-column layout: chat is always visible on the right
  
  const [requests, setRequests] = useState<MaintenanceRequest[]>([]);

  // Load recent requests for the tenant via master server (SQLite MCP)
  const leaseId = Number((import.meta as any)?.env?.VITE_LEASE_ID || (globalThis as any)?.__LEASE_ID || 1);
  const [requestsLoading, setRequestsLoading] = useState(true);
  const [requestsError, setRequestsError] = useState<string | null>(null);

  useEffect(() => {
    const loadRequests = async () => {
      try {
        setRequestsLoading(true);
        setRequestsError(null);
        
        const envBase = import.meta.env?.VITE_MASTER_SERVER_BASE as string | undefined;
        const winBase = (globalThis as any)?.__MASTER_SERVER_BASE as string | undefined;
        const storedBase = ((): string | undefined => { try { return localStorage.getItem('VITE_MASTER_SERVER_BASE') || undefined; } catch { return undefined; } })();
        const base = envBase || winBase || storedBase || 'http://localhost:8000';
        // Request a generous limit to show the full history for the demo
        const url = `${String(base).replace(/\/$/, "")}/tenant/requests?leaseId=${encodeURIComponent(String(leaseId))}&limit=1000`;

        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        
        const data = (await res.json()) as { items?: MaintenanceRequest[] };
        // console.log(data.items)
        const itemsRaw = Array.isArray(data?.items) ? data.items : [];
        // Keep normalization minimal: ensure expected shapes and status hyphenation
        const items: MaintenanceRequest[] = itemsRaw.map((r) => ({
          id: String(r.id),
          description: String(r.description || ""),
          urgency: (String(r.urgency || "medium") as MaintenanceRequest["urgency"]),
          category: String(r.category || "other"),
          status: (String(r.status || "open").replace(/_/g, "-") as MaintenanceRequest["status"]),
          date: String(r.date || "").slice(0, 10),
          image: (r as any).image,
        }));
        setRequests(items);
        console.log(`Loaded ${items.length} maintenance requests for lease ${leaseId}`);
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Failed to load requests';
        setRequestsError(errorMsg);
        console.error('Failed to load tenant requests:', error);
        toast({
          title: "Failed to load requests",
          description: `${errorMsg}. Ensure Master Server is running at VITE_MASTER_SERVER_BASE and SQLite is accessible.`,
          variant: "destructive",
        });
      } finally {
        setRequestsLoading(false);
      }
    };

    loadRequests();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leaseId]);

  // Workflows from shared JSON file (visible to both portals)
  const { workflows, refresh, loading: workflowsLoading, error: workflowsError } = useWorkflows({ pollMs: 10000 });
  const getWorkflowTitle = (w: WorkflowEntry) => (w.steps?.[0]?.title ?? "Planned workflow");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!description || !urgency || !category) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "Request Submitted",
      description: "Your maintenance request has been sent to your landlord.",
    });

    setDescription("");
    setUrgency("");
    setCategory("");
  };

  const handleRequestCreated = (request: MaintenanceRequest) => {
    setRequests(prev => [request, ...prev]);
    toast({
      title: "Request Created",
      description: `New request created from chat.`,
    });
  };

  const handleAssistantSent = (responseText: string, request: MaintenanceRequest) => {
    toast({
      title: "Sent to assistant",
      description: responseText?.slice(0, 140) || `Processed request ${request.id}`,
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "open":
        return <Clock className="h-4 w-4" />;
      case "in-progress":
        return <AlertTriangle className="h-4 w-4" />;
      case "resolved":
        return <CheckCircle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Header */}
      <header className="bg-background/80 backdrop-blur-sm border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 text-primary hover:text-primary/80 transition-colors">
              <ArrowLeft className="h-5 w-5" />
              Back to Portals
            </Link>
            <h1 className="text-xl font-semibold text-foreground">Tenant Portal</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Main two-column layout */}
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_420px]">
          {/* Left Column: Form + Recent Requests + Quick Actions */}
          <div className="space-y-6 min-w-0">
          {/* Request History */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle>Recent Requests</CardTitle>
              <CardDescription>
                Track the status of your maintenance requests
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {requestsLoading && (
                <div className="text-sm text-muted-foreground">Loading maintenance requests...</div>
              )}
              {requestsError && (
                <div className="text-sm text-destructive">Error: {requestsError}</div>
              )}
              {!requestsLoading && !requestsError && requests.length === 0 && (
                <div className="text-sm text-muted-foreground">No maintenance requests found.</div>
              )}
              <AnimatedList className="space-y-4">
                  {requests.map((request) => (
                    <div key={request.id} className="border rounded-lg p-4 space-y-3 hover:shadow-card transition-shadow">
                      <div className="flex items-start justify-between">
                        <span className="text-sm font-medium text-muted-foreground">
                          {request.id}
                        </span>
                        <Badge variant={request.status} className="flex items-center gap-1">
                          {getStatusIcon(request.status)}
                          {request.status.replace("-", " ")}
                        </Badge>
                      </div>
                      
                      <p className="text-sm leading-relaxed">{request.description}</p>
                      
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant={request.urgency}>
                          {request.urgency}
                        </Badge>
                        <span>•</span>
                        <span>{request.category}</span>
                        <span>•</span>
                        <span>{request.date}</span>
                      </div>
                    </div>
                  ))}
              </AnimatedList>
            </CardContent>
          </Card>

          {/* Shared Workflow Cards (read-only from workflows.json) */}
          <Card className="shadow-card">
            <CardHeader>
              <div className="flex items-center justify-between gap-2">
                <div>
                  <CardTitle>Workflow Updates</CardTitle>
                  <CardDescription>Steps created by the agent</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={refresh}>Refresh</Button>
              </div>
            </CardHeader>
            <CardContent>
              {workflowsError && (
                <div className="text-sm text-destructive">Failed to load workflows: {workflowsError}</div>
              )}
              {workflowsLoading && (
                <div className="text-sm text-muted-foreground">Loading workflows…</div>
              )}
              {!workflowsLoading && !workflowsError && workflows.length === 0 && (
                <div className="text-sm text-muted-foreground">No workflow entries yet.</div>
              )}

              <div className="space-y-3">
                {workflows.map((w) => (
                  <div key={w.id} className="border rounded-lg p-4 hover:shadow-card transition-shadow">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium text-sm">{getWorkflowTitle(w)}</h4>
                        <p className="text-xs text-muted-foreground mt-1">{w.prompt}</p>
                      </div>
                      <Badge variant="outline" className="text-[10px]">{new Date(w.createdAt).toLocaleString()}</Badge>
                    </div>
                    {w.steps && w.steps.length > 0 && (
                      <div className="mt-3 space-y-1">
                        {w.steps.map((s, idx) => (
                          <div key={idx} className="flex items-center gap-2 text-xs">
                            <Badge variant={s.status === 'done' ? 'success' : s.status === 'error' ? 'destructive' : 'secondary'}>{s.status}</Badge>
                            <span className="text-foreground">{s.title}</span>
                            {s.note && <span className="text-muted-foreground">— {s.note}</span>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          {/* Quick Actions */}
          <Card className="shadow-card">
            <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="outline" className="w-full justify-start">
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Knowledge
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Send className="h-4 w-4 mr-2" />
                  Contact Landlord
                </Button>
              </CardContent>
            </Card>
            {/* Submit Request Form*/}
            <Card className="shadow-elevated">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Send className="h-5 w-5 text-primary" />
                      Submit Maintenance Request
                    </CardTitle>
                    <CardDescription>
                      Describe your issue and we'll get it resolved quickly.
                    </CardDescription>
                  </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      placeholder="Describe the maintenance issue in detail..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="min-h-[120px] mt-2"
                      required
                    />
                  </div>

                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="urgency">Urgency Level</Label>
                      <Select value={urgency} onValueChange={setUrgency} required>
                        <SelectTrigger className="mt-2">
                          <SelectValue placeholder="Select urgency" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Low - Can wait a few days</SelectItem>
                          <SelectItem value="medium">Medium - Should be fixed soon</SelectItem>
                          <SelectItem value="high">High - Needs attention this week</SelectItem>
                          <SelectItem value="urgent">Urgent - Immediate attention needed</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="category">Category</Label>
                      <Select value={category} onValueChange={setCategory} required>
                        <SelectTrigger className="mt-2">
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="plumbing">Plumbing</SelectItem>
                          <SelectItem value="electrical">Electrical</SelectItem>
                          <SelectItem value="hvac">HVAC</SelectItem>
                          <SelectItem value="appliances">Appliances</SelectItem>
                          <SelectItem value="structural">Structural</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="image">Photo (Optional)</Label>
                    <Input
                      id="image"
                      type="file"
                      accept="image/*"
                      className="mt-2"
                    />
                    <p className="text-sm text-muted-foreground mt-1">
                      Upload a photo to help explain the issue
                    </p>
                  </div>

                  <Button type="submit" className="w-full" variant="hero">
                    <Send className="h-4 w-4 mr-2" />
                    Submit Request
                  </Button>
                </form>
                  </CardContent>
                </Card>
          </div>
          {/* Right Column: Chat (sticky) */}
          <div className="min-w-0">
            <div className="lg:sticky lg:top-24">
              <Chat 
                className="h-[calc(100vh-8rem)]"
                placeholder="Describe your maintenance issue... I'll help create a request!"
                onRequestCreated={handleRequestCreated}
                onAssistantSent={handleAssistantSent}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TenantPortal;
