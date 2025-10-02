import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Chat } from "@/components/ui/chat";
import { AnimatedList } from "@/components/ui/animated-list";
import { ArrowLeft, Users, Clock, CheckCircle, AlertTriangle, FileText, Plus } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useWorkflows, type WorkflowEntry, type WorkflowStep } from "@/hooks/useWorkflows";

interface MaintenanceRequest {
  id: string;
  tenant: string;
  description: string;
  urgency: "low" | "medium" | "high" | "urgent";
  category: string;
  status: "open" | "in-progress" | "resolved";
  date: string;
}

// Derived UI helpers for workflows.json entries
const firstStepTitle = (steps: WorkflowStep[] | undefined) => steps?.[0]?.title ?? "Planned workflow";
const statusFromSteps = (steps: WorkflowStep[] | undefined) => {
  if (!steps || steps.length === 0) return "pending" as const;
  const hasError = steps.some(s => s.status === "error");
  if (hasError) return "pending" as const;
  const allDone = steps.every(s => s.status === "done");
  return (allDone ? "done" : "in-progress") as const;
};

const LandlordPortal = () => {
  const { toast } = useToast();
  const [selectedRequest, setSelectedRequest] = useState<MaintenanceRequest | null>(null);
  // DnD + status animation state for workflow
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [overIndex, setOverIndex] = useState<number | null>(null);
  const [animatingDone, setAnimatingDone] = useState<Record<string, boolean>>({});
  
  const [requests, setRequests] = useState<MaintenanceRequest[]>([]);

  // Load maintenance requests for landlord via master server
  useEffect(() => {
    const envBase = import.meta.env?.VITE_MASTER_SERVER_BASE as string | undefined;
    const winBase = (globalThis as any)?.__MASTER_SERVER_BASE as string | undefined;
    const storedBase = ((): string | undefined => { try { return localStorage.getItem('VITE_MASTER_SERVER_BASE') || undefined; } catch { return undefined; } })();
    const base = envBase || winBase || storedBase || 'http://localhost:8000';
    const url = `${String(base).replace(/\/$/, "")}/landlord/requests`;
    (async () => {
      try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as { items?: any[] };
        const items = Array.isArray(data?.items) ? data.items : [];
        const mapped: MaintenanceRequest[] = items.map((it) => ({
          id: String(it.id ?? "").toUpperCase(),
          tenant: String(it.tenant ?? ""),
          description: String(it.description ?? ""),
          urgency: (String(it.urgency ?? "medium") as any),
          category: String(it.category ?? "other"),
          status: String(it.status ?? "open") as any,
          date: String(it.date ?? ""),
        }));
        setRequests(mapped);
      } catch {
        // ignore; keep empty
      }
    })();
  }, []);

  // Load workflows.json via hook
  const { workflows, refresh, loading: workflowsLoading, error: workflowsError } = useWorkflows({ pollMs: 10000 });
  // Map JSON entries to a simple card-like shape on the fly
  const workflowCards = useMemo(() => {
    return (workflows ?? []).map((w: WorkflowEntry) => ({
      id: w.id,
      title: firstStepTitle(w.steps),
      description: w.prompt,
      type: (w.result?.type ?? "other") as "task" | "document" | "maintenance" | "other",
      priority: "medium" as const,
      status: statusFromSteps(w.steps)
    }));
  }, [workflows]);

  const handleMarkResolved = (requestId: string) => {
    toast({
      title: "Request Marked Resolved",
      description: "The maintenance request has been marked as completed.",
    });
  };

  const handleNotifyTenant = (tenant: string) => {
    toast({
      title: "Notification Sent",
      description: `Update sent to ${tenant}`,
    });
  };

  const handleGenerateContract = () => {
    toast({
      title: "Action requires MCP",
      description: "Ask the agent to generate a contract; it will append to workflows.json.",
    });
  };

  const removeWorkflowCard = (_id: string) => {
    // Workflows come from file; removal is not persisted from UI in MVP
    toast({ title: "Not supported", description: "Remove requires MCP to update file." });
  };

  const markWorkflowDone = (id: string) => {
    setAnimatingDone(prev => ({ ...prev, [id]: true }));
    // Hide big checkmark after animation
    setTimeout(() => {
      setAnimatingDone(prev => ({ ...prev, [id]: false }));
    }, 1200);
  };

  // Drag & Drop handlers
  const handleDragStart = (index: number) => setDragIndex(index);
  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    setOverIndex(index);
  };
  const handleDrop = (index: number) => {
    // Reordering is not persisted in MVP (workflows come from file)
    setDragIndex(null);
    setOverIndex(null);
  };

  const handleRequestCreated = (request: MaintenanceRequest) => {
    setRequests(prev => [request, ...prev]);
    toast({
      title: "New Request Received",
      description: `Maintenance request from tenant: ${request.description.substring(0, 50)}...`,
    });
  };

  const handleAssistantSent = (responseText: string, request: MaintenanceRequest) => {
    toast({
      title: "Sent to assistant",
      description: responseText?.slice(0, 140) || `Processed request ${request.id}`,
    });
  };

  const stats = {
    totalOpen: requests.filter(r => r.status === "open").length,
    inProgress: requests.filter(r => r.status === "in-progress").length,
    avgResolution: "2.3 days"
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
            <h1 className="text-xl font-semibold text-foreground">Landlord Portal</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Stats Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Card className="shadow-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Open Requests</p>
                  <p className="text-2xl font-bold text-foreground">{stats.totalOpen}</p>
                </div>
                <Clock className="h-8 w-8 text-warning" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="shadow-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">In Progress</p>
                  <p className="text-2xl font-bold text-foreground">{stats.inProgress}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-primary" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="shadow-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Avg Resolution</p>
                  <p className="text-2xl font-bold text-foreground">{stats.avgResolution}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-success" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main two-column layout */}
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_420px]">
          {/* Left Column: Requests + Workflow + Quick Actions */}
          <div className="space-y-6 min-w-0">
            {/* Maintenance Requests Table */}
            <Card className="shadow-elevated">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-primary" />
                  Maintenance Requests
                </CardTitle>
                <CardDescription>
                  Manage and track all tenant maintenance requests
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Ticket ID</TableHead>
                      <TableHead>Tenant</TableHead>
                      <TableHead>Issue</TableHead>
                      <TableHead>Urgency</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {requests.map((request) => (
                      <TableRow 
                        key={request.id} 
                        className={request.urgency === "urgent" ? "bg-destructive/5 animate-pulse" : "hover:bg-muted/50 transition-colors"}
                      >
                        <TableCell className="font-medium">{request.id}</TableCell>
                        <TableCell>{request.tenant}</TableCell>
                        <TableCell className="max-w-xs truncate">{request.description}</TableCell>
                        <TableCell>
                          <Badge variant={request.urgency}>{request.urgency}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={request.status}>{request.status.replace("-", " ")}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Dialog>
                              <DialogTrigger asChild>
                                <Button 
                                  variant="outline" 
                                  size="sm"
                                  onClick={() => setSelectedRequest(request)}
                                >
                                  View
                                </Button>
                              </DialogTrigger>
                              <DialogContent className="max-w-2xl">
                                <DialogHeader>
                                  <DialogTitle>Request Details - {request.id}</DialogTitle>
                                  <DialogDescription>
                                    Maintenance request from {request.tenant}
                                  </DialogDescription>
                                </DialogHeader>
                                <div className="space-y-4">
                                  <div>
                                    <h4 className="font-semibold mb-2">Description</h4>
                                    <p className="text-sm text-muted-foreground">{request.description}</p>
                                  </div>
                                  <div className="grid grid-cols-2 gap-4">
                                    <div>
                                      <h4 className="font-semibold mb-2">Category</h4>
                                      <Badge variant="outline">{request.category}</Badge>
                                    </div>
                                    <div>
                                      <h4 className="font-semibold mb-2">Priority</h4>
                                      <Badge variant={request.urgency}>{request.urgency}</Badge>
                                    </div>
                                  </div>
                                  <div className="flex gap-2 pt-4">
                                    <Button 
                                      onClick={() => handleMarkResolved(request.id)}
                                      variant="success"
                                    >
                                      Mark Resolved
                                    </Button>
                                    <Button 
                                      onClick={() => handleNotifyTenant(request.tenant)}
                                      variant="outline"
                                    >
                                      Notify Tenant
                                    </Button>
                                  </div>
                                </div>
                              </DialogContent>
                            </Dialog>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
            {/* Workflow Section (scrollable if long) */}
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>Workflow</CardTitle>
                <CardDescription>
                  Drag to reorder, click × to remove tasks
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="max-h-[calc(100vh-16rem)] overflow-y-auto pr-1">
                  <AnimatedList className="space-y-3">
                    {workflowCards.map((card, index) => (
                      <div
                        key={card.id}
                        draggable
                        onDragStart={() => handleDragStart(index)}
                        onDragOver={(e) => handleDragOver(e, index)}
                        onDrop={() => handleDrop(index)}
                        className={
                          "relative border rounded-lg p-4 space-y-2 cursor-move transition-all duration-200 " +
                          (overIndex === index ? "ring-2 ring-primary/50 scale-[1.01] " : "") +
                          (dragIndex === index ? "opacity-70 " : "hover:shadow-card hover:scale-[1.02]")
                        }
                      >
                        {/* Big animated check overlay */}
                        {animatingDone[card.id] && (
                          <div className="absolute inset-0 bg-background/60 backdrop-blur-[1px] rounded-lg flex items-center justify-center pointer-events-none">
                            <CheckCircle className="h-16 w-16 text-success animate-check-pop" />
                          </div>
                        )}

                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium text-sm">{card.title}</h4>
                            {card.status === "done" && (
                              <Badge variant="success" className="text-[10px]">Done</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            {card.status !== "done" && (
                              <Button
                                variant="success"
                                size="sm"
                                onClick={() => markWorkflowDone(card.id)}
                                className="h-6 px-2 text-xs"
                              >
                                Mark done
                              </Button>
                            )}
                            <Button 
                              variant="ghost" 
                              size="sm"
                              aria-label="Remove"
                              onClick={() => removeWorkflowCard(card.id)}
                              className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive"
                            >
                              ×
                            </Button>
                          </div>
                        </div>
                        <p className="text-xs text-muted-foreground">{card.description}</p>
                        <div className="flex items-center gap-2">
                          <Badge variant={card.priority} className="text-xs">
                            {card.priority}
                          </Badge>
                          <span className="text-xs text-muted-foreground">•</span>
                          <span className="text-xs text-muted-foreground capitalize">{card.type}</span>
                        </div>
                      </div>
                    ))}
                  </AnimatedList>

                  {workflowsError && (
                    <div className="text-center py-6 text-destructive text-sm">
                      Failed to load workflows: {workflowsError}
                    </div>
                  )}

                  {workflowsLoading && (
                    <div className="text-center py-6 text-muted-foreground text-sm">
                      Loading workflows…
                    </div>
                  )}

                  {workflowCards.length === 0 && !workflowsLoading && !workflowsError && (
                    <div className="text-center py-8 text-muted-foreground">
                      <p className="text-sm">No active workflow items</p>
                      <p className="text-xs">Tasks will appear here automatically</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="shadow-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Quick Actions</CardTitle>
                  <Button variant="outline" size="sm" onClick={refresh}>Refresh Workflows</Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  onClick={handleGenerateContract}
                  variant="hero" 
                  className="w-full justify-start"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Generate Lease Contract
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Users className="h-4 w-4 mr-2" />
                  Manage Tenant Candidates
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Plus className="h-4 w-4 mr-2" />
                  Add New Property
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Chat (sticky) */}
          <div className="min-w-0">
            <div className="lg:sticky lg:top-24">
              <Chat
                className="h-[calc(100vh-8rem)]"
                placeholder="Type 'generate lease contract' or manage requests..."
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

export default LandlordPortal;
