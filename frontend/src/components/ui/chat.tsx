import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Paperclip, X, FileText, Image, File, Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

interface ChatMessage {
  id: string;
  content: string;
  type: "user" | "system";
  timestamp: Date;
  files?: ChatFile[];
}

interface ChatFile {
  id: string;
  name: string;
  size: number;
  type: string;
  url?: string;
}

interface ChatProps {
  className?: string;
  onMessageSend?: (message: string, files: ChatFile[]) => void;
  onRequestCreated?: (request: unknown) => void;
  onAssistantSent?: (responseText: string, request: unknown) => void;
  placeholder?: string;
}

export const Chat = ({ className, onMessageSend, onRequestCreated, onAssistantSent, placeholder = "Type a message..." }: ChatProps) => {
  const { toast } = useToast();
  const [message, setMessage] = useState("");
  const [files, setFiles] = useState<ChatFile[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      content: "Hello! I'm here to help you manage maintenance requests. You can describe issues and I'll help create requests automatically.",
      type: "system",
      timestamp: new Date()
    }
  ]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [ttsLoadingId, setTtsLoadingId] = useState<string | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const getServerBase = (): string => {
    const envBase = (import.meta as any)?.env?.VITE_MASTER_SERVER_BASE as string | undefined;
    const winBase = (globalThis as any)?.__MASTER_SERVER_BASE as string | undefined;
    const storedBase = (() => {
      try { return localStorage.getItem('VITE_MASTER_SERVER_BASE') || undefined; } catch { return undefined; }
    })();
    return (envBase || winBase || storedBase || 'http://localhost:8000').replace(/\/$/, "");
  };

  const speakText = async (text: string, id: string) => {
    const trimmed = (text || '').trim();
    if (!trimmed) return;
    try {
      setTtsLoadingId(id);
      const base = getServerBase();
      const voice = (import.meta as any)?.env?.VITE_TTS_VOICE as string | undefined;
      const voiceId = (import.meta as any)?.env?.VITE_TTS_VOICE_ID as string | undefined;
      const voiceName = (import.meta as any)?.env?.VITE_TTS_VOICE_NAME as string | undefined;
      const model = (import.meta as any)?.env?.VITE_TTS_MODEL as string | undefined;
      const payload: Record<string, unknown> = { text: trimmed, format: 'mp3' };
      if (voice) payload.voice = voice;
      if (voiceName) payload.voiceName = voiceName;
      if (voiceId) {
        payload.voiceId = voiceId;
        payload.voice_id = voiceId;
        payload.voiceCloneId = voiceId;
        payload.voice_clone_id = voiceId;
      }
      if (model) payload.model = model;
      const res = await fetch(`${base}/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        let errorMessage = `TTS failed (HTTP ${res.status})`;
        try {
          const data = await res.json();
          if (data?.detail && typeof data.detail === 'string') {
            errorMessage = data.detail;
          }
        } catch {}
        throw new Error(errorMessage);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      try { audioRef.current?.pause(); } catch {}
      audioRef.current = new Audio(url);
      await audioRef.current.play();
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'TTS playback failed';
      toast({ title: 'TTS error', description: msg, variant: 'destructive' });
    } finally {
      setTtsLoadingId(null);
    }
  };

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (!selectedFiles) return;
    
    const newFiles: ChatFile[] = Array.from(selectedFiles).map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
      url: URL.createObjectURL(file)
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
  };

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const parseMaintenanceRequest = (content: string) => {
    const lowerContent = content.toLowerCase();

    // Heuristic detection of maintenance requests
    const requestKeywords = ['leak', 'broken', 'not working', 'repair', 'fix', 'issue', 'problem', 'maintenance', 'heating', 'plumbing', 'electrical', 'hvac', 'light', 'outlet', 'appliance', 'dishwasher', 'washer', 'dryer'];
    const isRequest = requestKeywords.some(keyword => lowerContent.includes(keyword));
    if (!isRequest) return null;

    // Extract urgency
    let urgency: "low" | "medium" | "high" | "urgent" = "medium";
    if (lowerContent.includes('urgent') || lowerContent.includes('emergency') || lowerContent.includes('immediately')) {
      urgency = "urgent";
    } else if (lowerContent.includes('high') || lowerContent.includes('asap') || lowerContent.includes('quickly')) {
      urgency = "high";
    } else if (lowerContent.includes('low') || lowerContent.includes('when possible') || lowerContent.includes('eventually')) {
      urgency = "low";
    }

    // Extract category
    let category = "other";
    if (lowerContent.includes('leak') || lowerContent.includes('plumb') || lowerContent.includes('water') || lowerContent.includes('sink') || lowerContent.includes('toilet') || lowerContent.includes('faucet')) {
      category = "plumbing";
    } else if (lowerContent.includes('heat') || lowerContent.includes('hvac') || lowerContent.includes('air') || lowerContent.includes('temperature')) {
      category = "hvac";
    } else if (lowerContent.includes('light') || lowerContent.includes('electrical') || lowerContent.includes('power') || lowerContent.includes('outlet')) {
      category = "electrical";
    } else if (lowerContent.includes('appliance') || lowerContent.includes('refrigerator') || lowerContent.includes('stove') || lowerContent.includes('washer') || lowerContent.includes('dryer') || lowerContent.includes('dishwasher')) {
      category = "appliances";
    } else if (lowerContent.includes('wall') || lowerContent.includes('ceiling') || lowerContent.includes('floor') || lowerContent.includes('door') || lowerContent.includes('window')) {
      category = "structural";
    }

    return {
      id: `REQ${Date.now()}`,
      description: content,
      urgency,
      category,
      status: "open" as const,
      date: new Date().toISOString().split('T')[0],
      files: files.length > 0 ? files : undefined
    };
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() && files.length === 0) return;

    const newMessage: ChatMessage = {
      id: Math.random().toString(36).substr(2, 9),
      content: message,
      type: "user",
      timestamp: new Date(),
      files: files.length > 0 ? [...files] : undefined
    };

    setMessages(prev => [...prev, newMessage]);
    onMessageSend?.(message, files);

    // Check if this message looks like a maintenance request
    const request = parseMaintenanceRequest(message);
    if (request) {
      // Notify parent for local UI effects (toasts, tables)
      onRequestCreated?.(request);
    }

    // Always call Master MCP server and append its response as a system message
    const envBase = import.meta.env?.VITE_MASTER_SERVER_BASE as string | undefined;
    const winBase = (globalThis as any)?.__MASTER_SERVER_BASE as string | undefined;
    const storedBase = ((): string | undefined => {
      try { return localStorage.getItem('VITE_MASTER_SERVER_BASE') || undefined; } catch { return undefined; }
    })();
    const base = envBase || winBase || storedBase || 'http://localhost:8000';
    const url = `${base.replace(/\/$/, "")}/chat`;
    (async () => {
      try {
        // Try streaming endpoint first for progressive updates
        const streamUrl = `${base.replace(/\/$/, "")}/chat/stream`;
          const streamRes = await fetch(streamUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
            body: JSON.stringify({
              prompt: message,
              tenantEmail: (import.meta as any)?.env?.VITE_TENANT_EMAIL || (globalThis as any)?.__TENANT_EMAIL || undefined,
              leaseId: Number((import.meta as any)?.env?.VITE_LEASE_ID || (globalThis as any)?.__LEASE_ID || 1),
              meta: request ? { requestId: request.id } : undefined,
            }),
          });
        if (streamRes.ok && streamRes.body) {
          const reader = streamRes.body.getReader();
          const decoder = new TextDecoder();
          let sysId = Math.random().toString(36).substr(2, 9);
          let sysContent = "";
          setMessages(prev => [
            ...prev,
            { id: sysId, content: "", type: "system", timestamp: new Date() },
          ]);
          while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            const events = chunk.split(/\n\n/).filter(Boolean);
            for (const ev of events) {
              const line = ev.split("\n").find(l => l.startsWith("data:"));
              if (!line) continue;
              try {
                const payload = JSON.parse(line.slice(5).trim());
                if (payload.type === "text" && typeof payload.message === "string") {
                  sysContent += (sysContent ? " " : "") + payload.message;
                  setMessages(prev => prev.map(m => m.id === sysId ? { ...m, content: sysContent } : m));
                }
              } catch { /* ignore */ }
            }
          }
          onAssistantSent?.(sysContent || "", (request as unknown) ?? null);
          return; // streamed path handled
        }

        // Fallback to non-streaming endpoint
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt: message,
            tenantEmail: (import.meta as any)?.env?.VITE_TENANT_EMAIL || (globalThis as any)?.__TENANT_EMAIL || undefined,
            leaseId: Number((import.meta as any)?.env?.VITE_LEASE_ID || (globalThis as any)?.__LEASE_ID || 1),
            meta: request ? { requestId: request.id } : undefined,
          }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as { text?: string };
        const text = (data?.text && String(data.text).trim()) || (request ? `Request received. ID: ${request.id}` : "Got it — processing your message.");
        const systemResponse: ChatMessage = {
          id: Math.random().toString(36).substr(2, 9),
          content: text,
          type: "system",
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, systemResponse]);
        onAssistantSent?.(text, (request as unknown) ?? null);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Assistant request failed";
        toast({ title: "Assistant error", description: msg, variant: "destructive" });
        const fallback: ChatMessage = {
          id: Math.random().toString(36).substr(2, 9),
          content: request ? `I noted your request (${request.id}). Unable to reach assistant right now.` : "Unable to reach assistant right now.",
          type: "system",
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, fallback]);
      }
    })();

    setMessage("");
    setFiles([]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return <Image className="h-4 w-4" />;
    if (type.includes('text') || type.includes('document')) return <FileText className="h-4 w-4" />;
    return <File className="h-4 w-4" />;
  };

  return (
    <Card className={cn("flex flex-col h-[500px]", className)}>
      <CardContent className="flex flex-col h-full p-0">
        {/* Messages Area */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.map((msg) => (
              <div 
                key={msg.id} 
                className={cn(
                  "flex animate-fade-in",
                  msg.type === "user" ? "justify-end" : "justify-start"
                )}
              >
                <div 
                  className={cn(
                    "max-w-[80%] rounded-lg px-3 py-2 text-sm",
                    msg.type === "user" 
                      ? "bg-primary text-primary-foreground ml-4" 
                      : "bg-muted mr-4"
                  )}
                >
                  <p>{msg.content}</p>
                  {msg.files && msg.files.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {msg.files.map((file) => (
                        <div key={file.id} className="flex items-center gap-2 text-xs opacity-90">
                          {getFileIcon(file.type)}
                          <span className="truncate">{file.name}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {msg.type === "system" && msg.content?.trim() && (
                    <div className="mt-2 flex items-center gap-2">
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={() => speakText(msg.content, msg.id)}
                        disabled={ttsLoadingId === msg.id}
                        className="h-7 px-2"
                      >
                        <Volume2 className="h-4 w-4 mr-1" />
                        {ttsLoadingId === msg.id ? 'Playing...' : 'Play'}
                      </Button>
                    </div>
                  )}
                  <div className="text-xs opacity-70 mt-1">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div ref={messagesEndRef} />
        </ScrollArea>

        {/* File Upload Area */}
        {files.length > 0 && (
          <div className="border-t p-3 bg-muted/30">
            <div className="flex flex-wrap gap-2">
              {files.map((file) => (
                <Badge key={file.id} variant="secondary" className="flex items-center gap-1 pr-1">
                  {getFileIcon(file.type)}
                  <span className="truncate max-w-24">{file.name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(file.id)}
                    className="h-4 w-4 p-0 hover:bg-destructive hover:text-destructive-foreground"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div 
          className={cn(
            "border-t p-4 bg-background transition-colors",
            isDragging && "bg-muted border-primary"
          )}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <form onSubmit={handleSubmit} className="flex gap-2">
            <div className="flex-1 relative">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={placeholder}
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 p-0"
              >
                <Paperclip className="h-4 w-4" />
              </Button>
            </div>
            <Button type="submit" size="sm" disabled={!message.trim() && files.length === 0}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
          
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={(e) => handleFileSelect(e.target.files)}
            className="hidden"
            accept="image/*,.pdf,.doc,.docx,.txt"
          />
          
          {isDragging && (
            <div className="absolute inset-0 bg-primary/10 border-2 border-dashed border-primary rounded-lg flex items-center justify-center">
              <p className="text-primary font-medium">Drop files here to upload</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
