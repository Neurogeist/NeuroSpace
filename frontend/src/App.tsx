import { Box } from '@chakra-ui/react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Chat from './pages/Chat'
import RAGPage from './pages/RAG'
import LandingPage from './pages/LandingPage'

function App() {
  return (
    <Router>
      <Box minH="100vh" w="100vw" position="relative">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/rag" element={<RAGPage />} />
        </Routes>
      </Box>
    </Router>
  )
}

export default App
