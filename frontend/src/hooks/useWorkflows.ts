import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export type WorkflowStep = {
  title: string;
  status: "planned" | "done" | "error";
  note?: string;
};

export type WorkflowResult =
  | { type: "ticket"; data: Record<string, unknown> }
  | { type: "rent_details"; data: Record<string, unknown> }
  | { type: "other"; data: Record<string, unknown> };

export type WorkflowEntry = {
  id: string;
  createdAt: string; // ISO8601
  prompt: string;
  steps: WorkflowStep[];
  result?: WorkflowResult;
};

type UseWorkflowsOptions = {
  pollMs?: number;
  cacheBust?: boolean;
};

export function useWorkflows(options: UseWorkflowsOptions = {}) {
  const { pollMs = 0, cacheBust = true } = options;
  const [workflows, setWorkflows] = useState<WorkflowEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const load = useCallback(async () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const base = "/workflows.json";
      const url = cacheBust ? `${base}?cb=${Date.now()}` : base;
      const res = await fetch(url, { signal: controller.signal });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as unknown;
      const arr = Array.isArray(json) ? (json as WorkflowEntry[]) : [];
      setWorkflows(arr);
    } catch (e: unknown) {
      const err = e as { name?: unknown; message?: unknown };
      const isAbort = typeof err?.name === "string" && err.name === "AbortError";
      if (!isAbort) {
        const msg = typeof err?.message === "string" ? err.message : "Failed to load workflows";
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }, [cacheBust]);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!pollMs || pollMs <= 0) return;
    const id = setInterval(load, pollMs);
    return () => clearInterval(id);
  }, [pollMs, load]);

  return { workflows, refresh: load, loading, error } as const;
}
