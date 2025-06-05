import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getAvailableModels, getSessions, ChatSession } from '../services/api';
import { ethers } from 'ethers';
import { useAccount, useWalletClient } from 'wagmi';

interface AppContextType {
  userAddress: string | null;
  provider: ethers.BrowserProvider | null;
  models: { [key: string]: string };
  sessions: ChatSession[];
  isLoadingModels: boolean;
  isLoadingSessions: boolean;
  error: string | null;
  refreshSessions: () => Promise<void>;
  refreshModels: () => Promise<void>;
  isApproved: boolean;
  setIsApproved: (approved: boolean) => void;
  tokenBalance: string;
  setTokenBalance: (balance: string) => void;
  remainingFreeRequests: number;
  setRemainingFreeRequests: (count: number) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const { address } = useAccount();
  const { data: walletClient } = useWalletClient();
  const [provider, setProvider] = useState<ethers.BrowserProvider | null>(null);
  const [models, setModels] = useState<{ [key: string]: string }>({});
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isApproved, setIsApproved] = useState(false);
  const [tokenBalance, setTokenBalance] = useState<string>('0');
  const [remainingFreeRequests, setRemainingFreeRequests] = useState<number>(0);

  // Update provider when wallet client changes
  useEffect(() => {
    if (walletClient) {
      const provider = new ethers.BrowserProvider(walletClient as any);
      setProvider(provider);
    } else {
      setProvider(null);
    }
  }, [walletClient]);

  // --- Model Loading ---
  const loadModels = useCallback(async () => {
    setIsLoadingModels(true);
    try {
      if (!address || !provider) {
        console.log('No user address or provider available, skipping model load');
        setModels({});
        return;
      }

      const modelsData = await getAvailableModels(address, provider);
      setModels(modelsData);
      setError(null);
    } catch (err) {
      console.error('Error loading models:', err);
      setError(err instanceof Error ? err.message : 'Failed to load models');
      setModels({});
    } finally {
      setIsLoadingModels(false);
    }
  }, [address, provider]);

  // --- Session Loading ---
  const loadSessions = useCallback(async (userAddress: string) => {
    if (!provider) {
      console.log('Provider not available yet, skipping session load');
      return;
    }

    setIsLoadingSessions(true);
    try {
      const sessionsData = await getSessions(userAddress, provider);
      setSessions(sessionsData);
      setError(null);
    } catch (err) {
      console.error('Error loading sessions:', err);
      setError(err instanceof Error ? err.message : 'Failed to load sessions');
      setSessions([]);
    } finally {
      setIsLoadingSessions(false);
    }
  }, [provider]);

  const refreshSessions = useCallback(async () => {
    if (address) {
      await loadSessions(address);
    }
  }, [address, loadSessions]);

  const refreshModels = useCallback(async () => {
    await loadModels();
  }, [loadModels]);

  // --- Initial Data Loading Effects ---
  useEffect(() => {
    if (address && provider) {
      loadModels();
    }
  }, [address, provider, loadModels]);

  useEffect(() => {
    if (address) {
      loadSessions(address);
    } else {
      setSessions([]);
      setIsLoadingSessions(false);
    }
  }, [address, loadSessions]);

  return (
    <AppContext.Provider
      value={{
        userAddress: address || null,
        provider,
        models,
        sessions,
        isLoadingModels,
        isLoadingSessions,
        error,
        refreshSessions,
        refreshModels,
        isApproved,
        setIsApproved,
        tokenBalance,
        setTokenBalance,
        remainingFreeRequests,
        setRemainingFreeRequests
      }}
    >
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