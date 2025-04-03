import { Box, IconButton, useColorMode, useColorModeValue } from '@chakra-ui/react'
import { Chat } from './components/Chat'
import { FiSun, FiMoon } from 'react-icons/fi'

function App() {
  const { colorMode, toggleColorMode } = useColorMode()
  const bgColor = useColorModeValue('gray.50', 'gray.900')
  const iconColor = useColorModeValue('gray.600', 'gray.300')

  return (
    <Box minH="100vh" w="100vw" bg={bgColor} position="relative">
      <IconButton
        aria-label="Toggle color mode"
        icon={colorMode === 'light' ? <FiMoon /> : <FiSun />}
        onClick={toggleColorMode}
        position="fixed"
        top={4}
        right={4}
        zIndex={1000}
        colorScheme="blue"
        variant="ghost"
        color={iconColor}
      />
      <Chat />
    </Box>
  )
}

export default App
