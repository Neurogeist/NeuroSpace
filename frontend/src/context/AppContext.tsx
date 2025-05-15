import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getAvailableModels, getSessions, ChatSession } from '../services/api'; // Assuming ChatSession is exported from api or types
import { connectWallet as connectWalletService } from '../services/blockchain'; // Import your actual connect service

interface AppContextType {
  userAddress: string | null; // Add userAddress state
  connectWallet: () => Promise<string | null>; // Add connect function
  models: { [key: string]: string };
  sessions: ChatSession[]; // Use correct type if available
  isLoadingModels: boolean; // Separate loading states
  isLoadingSessions: boolean; // Separate loading states
  error: string | null;
  refreshSessions: () => Promise<void>;
  refreshModels: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [userAddress, setUserAddress] = useState<string | null>(null); // Wallet address state
  const [models, setModels] = useState<{ [key: string]: string }>({});
  const [sessions, setSessions] = useState<ChatSession[]>([]); // Use specific type
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false); // Initially false, load sessions only when address is known
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const tryAutoConnect = async () => {
      if (!userAddress) {
        try {
          const address = await connectWalletService(); // Or use injected `window.ethereum` manually
          setUserAddress(address);
          console.log("🔁 Auto-connected wallet:", address);
        } catch (err) {
          console.warn("⚠️ Auto-connect failed or wallet not available");
        }
      }
    };
  
    tryAutoConnect();
  }, []);
  

  // --- Wallet Connection ---
  const connectWallet = async (): Promise<string | null> => {
    try {
      const address = await connectWalletService();
      setUserAddress(address);
      setError(null); // Clear previous errors on successful connect
      console.log("Wallet connected in context:", address);
      return address;
    } catch (err) {
      console.error('Error connecting wallet in context:', err);
      setUserAddress(null); // Ensure address is null on error
      setSessions([]); // Clear sessions if wallet disconnects or fails to connect
      setError(err instanceof Error ? err.message : 'Failed to connect wallet');
      return null;
    }
  };

  // --- Model Loading ---
  const loadModels = useCallback(async () => {
    setIsLoadingModels(true);
    try {
      const modelsData = await getAvailableModels();
      setModels(modelsData);
      setError(null);
    } catch (err) {
      console.error('Error loading models:', err);
      setError(err instanceof Error ? err.message : 'Failed to load models');
      setModels({}); // Clear models on error
    } finally {
      setIsLoadingModels(false);
    }
  }, []); // No dependencies, models don't depend on user address

  // --- Session Loading (Depends on userAddress) ---
  const loadSessions = useCallback(async (address: string | null) => {
    // Only load if address is valid
    if (!address) {
      console.log("No address provided to loadSessions, clearing sessions.");
      setSessions([]); // Clear sessions if no address
      setIsLoadingSessions(false);
      return;
    }

    // Remove sensitive address logging
    // console.log(`Context: Attempting to load sessions for ${address}`);
    setIsLoadingSessions(true);
    setError(null);
    try {
      // CORRECTED: Pass the address to getSessions
      const sessionsData = await getSessions(address);
      setSessions(sessionsData);

      // Validate active session (optional, but good practice)
      const activeSessionId = localStorage.getItem('activeSessionId');
      if (activeSessionId && sessionsData.length > 0) {
        const sessionExists = sessionsData.some(session => session.session_id === activeSessionId);
        if (!sessionExists) {
          console.log(`Context: Active session ${activeSessionId} not found in loaded sessions, clearing local storage.`);
          localStorage.removeItem('activeSessionId');
        }
      } else if (activeSessionId) {
         // Clear if there are no sessions but local storage still has an ID
         localStorage.removeItem('activeSessionId');
      }

    } catch (err) {
      console.error('Error loading sessions in context:', err instanceof Error ? err.message : 'Unknown error');
      setError(err instanceof Error ? err.message : 'Failed to load sessions');
      setSessions([]); // Clear sessions on error
    } finally {
      setIsLoadingSessions(false);
    }
  }, []); // Depends on the function itself, not external state changes here

  // Function exposed to components for refreshing sessions
  const refreshSessions = async () => {
    // Uses the current userAddress from state
    await loadSessions(userAddress);
  };

  // Function exposed for refreshing models
  const refreshModels = async () => {
    await loadModels();
  };

  // --- Initial Data Loading Effects ---

  // Load models once on mount
  useEffect(() => {
    loadModels();
  }, [loadModels]);

  // Load sessions whenever the userAddress changes
  useEffect(() => {
    if (userAddress) {
      loadSessions(userAddress);
    } else {
      // If user disconnects (address becomes null), clear sessions
      setSessions([]);
      setIsLoadingSessions(false); // Ensure loading is stopped
    }
  }, [userAddress, loadSessions]); // Run when address changes or loadSessions definition changes

  return (
    <AppContext.Provider
      value={{
        userAddress,
        connectWallet,
        models,
        sessions,
        isLoadingModels,
        isLoadingSessions,
        error,
        refreshSessions,
        refreshModels,
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