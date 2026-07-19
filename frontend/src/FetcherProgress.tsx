import { useEffect, useRef, useState, createContext, useContext, useCallback } from "react";
import { api } from "./api/client";

interface FetcherProgress {
  running: boolean;
  percent: number;
  message: string;
  step: string;
  details: Record<string, number>;
  elapsed_seconds?: number;
}

interface FetcherCtx {
  progress: FetcherProgress | null;
  running: boolean;
  startFetcher: () => void;
}

const FetcherContext = createContext<FetcherCtx>({
  progress: null,
  running: false,
  startFetcher: () => {},
});

export function useFetcher() {
  return useContext(FetcherContext);
}

const PLACEHOLDER: FetcherProgress = {
  running: true,
  percent: 0,
  message: "Starting fetcher...",
  step: "starting",
  details: {},
};

export function FetcherProvider({ children }: { children: React.ReactNode }) {
  const [progress, setProgress] = useState<FetcherProgress | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const aliveRef = useRef(true);

  useEffect(() => {
    aliveRef.current = true;
    connectWS();
    return () => {
      aliveRef.current = false;
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  function connectWS() {
    if (!aliveRef.current) return;
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${proto}//${location.host}/ws/fetcher/progress/`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[WS] Connected");
    };

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.running) {
        setProgress({
          running: true,
          percent: msg.percent || 0,
          message: msg.message || "Working...",
          step: msg.step || "",
          details: msg.details || {},
          elapsed_seconds: msg.elapsed_seconds,
        });
      } else {
        setProgress((prev) => {
          if (!prev?.running) return null;
          return {
            running: false,
            percent: 100,
            message: msg.message || "Done!",
            step: "done",
            details: msg.details || prev.details,
            elapsed_seconds: msg.elapsed_seconds,
          };
        });
        setTimeout(() => setProgress(null), 5000);
      }
    };

    ws.onclose = () => {
      console.log("[WS] Disconnected, reconnecting in 3s...");
      setTimeout(() => connectWS(), 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }

  const startFetcher = useCallback(async () => {
    setProgress(PLACEHOLDER);
    try {
      await api.fetcher.run();
    } catch {
      setProgress(null);
    }
  }, []);

  const running = progress?.running ?? false;

  return (
    <FetcherContext.Provider value={{ progress, running, startFetcher }}>
      {children}
    </FetcherContext.Provider>
  );
}
