import React from 'react';
import { WagmiConfig, createConfig } from 'wagmi';
import { base, baseSepolia } from 'wagmi/chains';
import { http } from 'wagmi';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Box, ChakraProvider, CSSReset } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Chat from './pages/Chat';
import RAGPage from './pages/RAG';
import LandingPage from './pages/LandingPage';
import Documentation from './pages/Documentation';
import AgentsPage from './pages/Agents';
import Navigation from './components/Navigation';
import { theme } from './theme';
import { useColorModeValue } from '@chakra-ui/react';
import './App.css';

// Create a client
const queryClient = new QueryClient();

// Create wagmi config with required transports and connectors
const config = createConfig({
  chains: [base, baseSepolia],
  transports: {
    [base.id]: http(),
    [baseSepolia.id]: http(),
  },
});

function AppContent() {
  const location = useLocation();
  const isChatPage = location.pathname === '/chat';
  const bgColor = useColorModeValue('white', 'gray.900');

  return (
    <Box 
      minH="100vh" 
      position="relative" 
      bg={bgColor}
    >
      {!isChatPage && <Navigation />}
      <Box pt={isChatPage ? 0 : "64px"}>
        <AnimatePresence mode="wait">
          <Routes>
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
    <QueryClientProvider client={queryClient}>
      <WagmiConfig config={config}>
        <ChakraProvider theme={theme}>
          <CSSReset />
          <Router>
            <AppContent />
          </Router>
        </ChakraProvider>
      </WagmiConfig>
    </QueryClientProvider>
  );
}

export default App;
