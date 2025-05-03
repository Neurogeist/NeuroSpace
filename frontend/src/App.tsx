import { Box } from '@chakra-ui/react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Chat from './components/Chat'
import RAGPage from './pages/RAG'

function App() {
  return (
    <Router>
      <Box minH="100vh" w="100vw" position="relative">
        <Routes>
          <Route path="/" element={<Chat />} />
          <Route path="/rag" element={<RAGPage />} />
        </Routes>
      </Box>
    </Router>
  )
}

export default App
