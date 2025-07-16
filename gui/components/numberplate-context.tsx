"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

// Define the context type
interface NumberPlateContextType {
  currentNumber: number | null;
  connectionStatus: string;
  lastUpdate: string;
}

// Create the context
const NumberPlateContext = createContext<NumberPlateContextType | undefined>(undefined);

// Provider component
interface NumberPlateProviderProps {
  children: ReactNode;
}

export function NumberPlateProvider({ children }: NumberPlateProviderProps) {
  const [currentNumber, setCurrentNumber] = useState<number | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>("Disconnected");
  const [lastUpdate, setLastUpdate] = useState<string>("");

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_MONITOR_SERVER || "ws://localhost:8000";
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnectionStatus("Connected");
      console.log("Connected to WebSocket server");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "number_detected") {
          setCurrentNumber(data.number);
          setLastUpdate(new Date(data.timestamp).toLocaleTimeString());
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    ws.onclose = () => {
      setConnectionStatus("Disconnected");
      console.log("Disconnected from WebSocket server");
    };

    ws.onerror = (error) => {
      setConnectionStatus("Error");
      console.error("WebSocket error:", error);
    };

    return () => {
      ws.close();
    };
  }, []);

  const value = {
    currentNumber,
    connectionStatus,
    lastUpdate,
  };

  return (
    <NumberPlateContext.Provider value={value}>
      {children}
    </NumberPlateContext.Provider>
  );
}

// Custom hook to use the context
export function useNumberPlate() {
  const context = useContext(NumberPlateContext);
  if (context === undefined) {
    throw new Error("useNumberPlate must be used within a NumberPlateProvider");
  }
  return context;
}
