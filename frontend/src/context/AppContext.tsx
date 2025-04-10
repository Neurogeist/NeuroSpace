import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { getAvailableModels, getSessions } from '../services/api';

interface AppContextType {
  models: { [key: string]: string };
  sessions: any[];
  isLoading: boolean;
  error: string | null;
  refreshSessions: () => Promise<void>;
  refreshModels: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [models, setModels] = useState<{ [key: string]: string }>({});
  const [sessions, setSessions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const initialLoadRef = useRef(false);

  const loadModels = async () => {
    try {
      const modelsData = await getAvailableModels();
      setModels(modelsData);
    } catch (err) {
      console.error('Error loading models:', err);
      setError(err instanceof Error ? err.message : 'Failed to load models');
    }
  };

  const loadSessions = async () => {
    try {
      const sessionsData = await getSessions();
      setSessions(sessionsData);
    } catch (err) {
      console.error('Error loading sessions:', err);
      setError(err instanceof Error ? err.message : 'Failed to load sessions');
    }
  };

  const loadInitialData = async () => {
    if (initialLoadRef.current) return;
    initialLoadRef.current = true;

    try {
      setIsLoading(true);
      await Promise.all([loadModels(), loadSessions()]);
    } catch (err) {
      console.error('Error loading initial data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  };

  const refreshSessions = async () => {
    await loadSessions();
  };

  const refreshModels = async () => {
    await loadModels();
  };

  useEffect(() => {
    loadInitialData();

    return () => {
      initialLoadRef.current = false;
    };
  }, []);

  return (
    <AppContext.Provider value={{ models, sessions, isLoading, error, refreshSessions, refreshModels }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
} 