import {
  Box,
  Flex,
  HStack,
  IconButton,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useDisclosure,
  useColorModeValue,
  Stack,
  useColorMode,
  Container,
  Text,
  Image,
  Link,
  SlideFade
} from '@chakra-ui/react'
import { HamburgerIcon, CloseIcon, MoonIcon, SunIcon } from '@chakra-ui/icons'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'

const Links = [
  { name: 'Chat', path: '/chat' },
  { name: 'RAG', path: '/rag' },
  { name: 'Documentation', path: '/docs' },
]

const NavLink = ({ children, to }: { children: React.ReactNode; to: string }) => {
  const location = useLocation()
  const isActive = location.pathname === to
  const bgColor = useColorModeValue('blue.50', 'blue.900')
  const textColor = useColorModeValue('blue.600', 'blue.200')

  return (
    <Link
      as={RouterLink}
      to={to}
      px={4}
      py={2}
      rounded="md"
      fontWeight="medium"
      _hover={{
        textDecoration: 'none',
        bg: bgColor,
        color: textColor,
      }}
      bg={isActive ? bgColor : 'transparent'}
      color={isActive ? textColor : 'inherit'}
      transition="all 0.2s"
    >
      {children}
    </Link>
  )
}

export default function Navigation() {
  const { isOpen, onToggle } = useDisclosure()
  const { colorMode, toggleColorMode } = useColorMode()
  const [isScrolled, setIsScrolled] = useState(false)
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <Box
      position="fixed"
      w="100%"
      zIndex={1000}
      transition="all 0.3s"
      bg={bgColor}
      borderBottom="1px"
      borderColor={isScrolled ? borderColor : 'transparent'}
      boxShadow={isScrolled ? 'sm' : 'none'}
    >
      <Container maxW="container.xl">
        <Flex h={16} alignItems="center" justifyContent="space-between">
          <IconButton
            size="md"
            icon={isOpen ? <CloseIcon /> : <HamburgerIcon />}
            aria-label="Open Menu"
            display={{ md: 'none' }}
            onClick={onToggle}
          />

          <HStack spacing={8} alignItems="center">
            <Link as={RouterLink} to="/" _hover={{ textDecoration: 'none' }}>
              <HStack spacing={2}>
                <Image
                  src="/logo.png"
                  alt="NeuroSpace"
                  fallbackSrc="https://via.placeholder.com/32"
                  boxSize="32px"
                />
                <Text
                  fontWeight="bold"
                  fontSize="lg"
                  bgGradient="linear(to-r, blue.400, purple.500)"
                  bgClip="text"
                >
                  NeuroSpace
                </Text>
              </HStack>
            </Link>

            <HStack as="nav" spacing={4} display={{ base: 'none', md: 'flex' }}>
              {Links.map((link) => (
                <NavLink key={link.path} to={link.path}>
                  {link.name}
                </NavLink>
              ))}
            </HStack>
          </HStack>

          <Flex alignItems="center">
            <Button
              variant="ghost"
              onClick={toggleColorMode}
              mr={4}
              aria-label="Toggle color mode"
            >
              {colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
            </Button>
            <Button
              as={RouterLink}
              to="/chat"
              colorScheme="blue"
              display={{ base: 'none', md: 'inline-flex' }}
            >
              Get Started
            </Button>
          </Flex>
        </Flex>

        <SlideFade in={isOpen} offsetY="-20px">
          <Box
            pb={4}
            display={{ md: 'none' }}
            borderTop="1px"
            borderColor={borderColor}
          >
            <Stack as="nav" spacing={4}>
              {Links.map((link) => (
                <NavLink key={link.path} to={link.path}>
                  {link.name}
                </NavLink>
              ))}
              <Button
                as={RouterLink}
                to="/chat"
                colorScheme="blue"
                w="full"
              >
                Get Started
              </Button>
            </Stack>
          </Box>
        </SlideFade>
      </Container>
    </Box>
  )
} 