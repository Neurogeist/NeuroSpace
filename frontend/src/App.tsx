import { Box, ChakraProvider, CSSReset } from '@chakra-ui/react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import Chat from './pages/Chat'
import RAGPage from './pages/RAG'
import LandingPage from './pages/LandingPage'
import Documentation from './pages/Documentation'
import Navigation from './components/Navigation'
import { theme } from './theme'
import { useColorModeValue } from '@chakra-ui/react'

function AppContent() {
  const location = useLocation()
  const isChatPage = location.pathname === '/chat'
  const bgColor = useColorModeValue('white', 'gray.900')

  return (
    <Box 
      minH="100vh" 
      w="100vw" 
      position="relative" 
      bg={bgColor}
      overflowX="hidden"
    >
      {!isChatPage && <Navigation />}
      <Box pt={isChatPage ? 0 : "64px"}>
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/rag" element={<RAGPage />} />
            <Route path="/docs" element={<Documentation />} />
          </Routes>
        </AnimatePresence>
      </Box>
    </Box>
  )
}

function App() {
  return (
    <ChakraProvider theme={theme}>
      <CSSReset />
      <Router>
        <AppContent />
      </Router>
    </ChakraProvider>
  )
}

export default App
