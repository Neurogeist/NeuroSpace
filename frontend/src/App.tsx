import React from 'react';
import { createWeb3Modal } from '@web3modal/wagmi/react';
import { WagmiProvider, http, createConfig } from 'wagmi';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Box, ChakraProvider, CSSReset } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { base, baseSepolia } from 'wagmi/chains';
import { useAccount } from 'wagmi';
import { theme } from './theme';
import Navigation from './components/Navigation';
import { AppProvider } from './context/AppContext';
import Chat from './pages/Chat';
import RAGPage from './pages/RAG';
import LandingPage from './pages/LandingPage';
import Documentation from './pages/Documentation';
import AgentsPage from './pages/Agents';
import './App.css';

const projectId = '42646914ef3f478b688716921690e7ea';
const ENVIRONMENT = import.meta.env.VITE_ENVIRONMENT || 'development';

const wagmiConfig = createConfig({
  chains: ENVIRONMENT === 'development' ? [baseSepolia] : [base],
  transports: {
    [baseSepolia.id]: http(),
    [base.id]: http()
  }
});

createWeb3Modal({
  wagmiConfig,
  projectId
});

const queryClient = new QueryClient();

function TestComponent() {
  const { address, isConnected } = useAccount();
  return (
    <Box p={4}>
      <h1>Wallet Status</h1>
      <p>Connected: {isConnected ? 'Yes' : 'No'}</p>
      <p>Address: {address}</p>
    </Box>
  );
}

function AppContent() {
  const location = useLocation();
  const isChatPage = location.pathname === '/chat';

  return (
    <Box minH="100vh">
      {!isChatPage && <Navigation />}
      <Box pt={isChatPage ? 0 : "64px"}>
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/rag" element={<RAGPage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/docs" element={<Documentation />} />
          </Routes>
        </AnimatePresence>
      </Box>
    </Box>
  );
}

function App() {
  return (
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={queryClient}>
        <ChakraProvider theme={theme}>
          <CSSReset />
          <Router>
            <AppProvider>
              <AppContent />
            </AppProvider>
          </Router>
        </ChakraProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}

export default App;
