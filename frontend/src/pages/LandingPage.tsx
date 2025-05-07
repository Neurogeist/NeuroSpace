import {
  Box,
  Container,
  Heading,
  Text,
  Button,
  VStack,
  HStack,
  SimpleGrid,
  Icon,
  useColorModeValue,
  Flex,
  Image,
  Stack,
  useBreakpointValue
} from '@chakra-ui/react'
import { useNavigate } from 'react-router-dom'
import { FaRobot, FaDatabase, FaLock, FaBolt } from 'react-icons/fa'

const Feature = ({ title, text, icon }: { title: string; text: string; icon: any }) => {
  return (
    <Stack
      spacing={4}
      align="center"
      textAlign="center"
      p={6}
      bg={useColorModeValue('white', 'gray.800')}
      rounded="xl"
      shadow="lg"
      _hover={{ transform: 'translateY(-5px)', transition: 'all 0.3s ease' }}
    >
      <Flex
        w={16}
        h={16}
        align="center"
        justify="center"
        color="white"
        rounded="full"
        bg="blue.500"
        mb={1}
      >
        <Icon as={icon} w={8} h={8} />
      </Flex>
      <Text fontWeight={600} fontSize="xl">
        {title}
      </Text>
      <Text color={useColorModeValue('gray.600', 'gray.400')}>
        {text}
      </Text>
    </Stack>
  )
}

const LandingPage = () => {
  const navigate = useNavigate()
  const bgColor = useColorModeValue('gray.50', 'gray.900')
  const textColor = useColorModeValue('gray.600', 'gray.400')
  const headingColor = useColorModeValue('gray.800', 'white')

  return (
    <Box bg={bgColor}>
      {/* Hero Section */}
      <Container maxW="container.xl" py={20}>
        <Stack
          direction={{ base: 'column', md: 'row' }}
          spacing={8}
          align="center"
          justify="space-between"
        >
          <Stack spacing={6} maxW="600px">
            <Heading
              size="2xl"
              color={headingColor}
              lineHeight="1.2"
              fontWeight="bold"
            >
              Welcome to NeuroSpace
            </Heading>
            <Text fontSize="xl" color={textColor}>
              Experience the future of AI-powered blockchain interactions. 
              Chat with advanced AI models and explore our powerful RAG system.
            </Text>
            <HStack spacing={4}>
              <Button
                colorScheme="blue"
                size="lg"
                onClick={() => navigate('/chat')}
                px={8}
                _hover={{ transform: 'translateY(-2px)', shadow: 'lg' }}
              >
                Try Chat
              </Button>
              <Button
                colorScheme="purple"
                size="lg"
                onClick={() => navigate('/rag')}
                px={8}
                _hover={{ transform: 'translateY(-2px)', shadow: 'lg' }}
              >
                Explore RAG
              </Button>
            </HStack>
          </Stack>
          <Box
            display={{ base: 'none', md: 'block' }}
            maxW="500px"
            w="100%"
          >
            <Image
              src="/hero-image.png"
              alt="NeuroSpace AI"
              fallbackSrc="https://via.placeholder.com/500x400"
              rounded="lg"
              shadow="2xl"
            />
          </Box>
        </Stack>
      </Container>

      {/* Features Section */}
      <Box py={20} bg={useColorModeValue('white', 'gray.800')}>
        <Container maxW="container.xl">
          <VStack spacing={12}>
            <Stack spacing={4} textAlign="center">
              <Heading color={headingColor}>Powerful Features</Heading>
              <Text fontSize="lg" color={textColor} maxW="600px">
                Discover the capabilities that make NeuroSpace unique
              </Text>
            </Stack>

            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={10}>
              <Feature
                icon={FaRobot}
                title="Advanced AI Chat"
                text="Interact with state-of-the-art AI models for intelligent conversations"
              />
              <Feature
                icon={FaDatabase}
                title="RAG System"
                text="Retrieve and generate responses using your own knowledge base"
              />
              <Feature
                icon={FaLock}
                title="Blockchain Security"
                text="Secure transactions and interactions powered by blockchain technology"
              />
              <Feature
                icon={FaBolt}
                title="Lightning Fast"
                text="Experience quick responses and seamless interactions"
              />
            </SimpleGrid>
          </VStack>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box py={20}>
        <Container maxW="container.xl">
          <Stack
            direction={{ base: 'column', md: 'row' }}
            spacing={8}
            align="center"
            justify="space-between"
            bg={useColorModeValue('blue.50', 'blue.900')}
            p={8}
            rounded="xl"
          >
            <Stack spacing={4} maxW="600px">
              <Heading size="lg" color={headingColor}>
                Ready to Get Started?
              </Heading>
              <Text fontSize="lg" color={textColor}>
                Join NeuroSpace today and experience the future of AI-powered interactions
              </Text>
            </Stack>
            <Button
              colorScheme="blue"
              size="lg"
              onClick={() => navigate('/chat')}
              px={8}
              _hover={{ transform: 'translateY(-2px)', shadow: 'lg' }}
            >
              Start Now
            </Button>
          </Stack>
        </Container>
      </Box>
    </Box>
  )
}

export default LandingPage 