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
  Badge,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
} from '@chakra-ui/react'
import { useNavigate } from 'react-router-dom'
import { FaRobot, FaDatabase, FaShieldAlt, FaCheckCircle, FaNetworkWired, FaCoins, FaEdit, FaMagic, FaKey, FaLink, FaFileAlt, FaDownload } from 'react-icons/fa'

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

const HowItWorksStep = ({ step, title, text, icon }: { step: number; title: string; text: string; icon: any }) => {
  return (
    <Stack
      spacing={4}
      align="center"
      textAlign="center"
      p={6}
      bg={useColorModeValue('white', 'gray.800')}
      rounded="xl"
      shadow="lg"
      position="relative"
      _hover={{ transform: 'translateY(-5px)', transition: 'all 0.3s ease' }}
    >
      <Badge
        position="absolute"
        top={-3}
        right={-3}
        colorScheme="blue"
        rounded="full"
        px={3}
        py={1}
        fontSize="sm"
      >
        Step {step}
      </Badge>
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
  const accentColor = useColorModeValue('blue.500', 'blue.300')
  const { isOpen, onOpen, onClose } = useDisclosure()

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
            <Badge
              colorScheme="blue"
              alignSelf="start"
              px={3}
              py={1}
              rounded="full"
              fontSize="sm"
            >
              Trust in AI, Mathematically Enforced
            </Badge>
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
            <HStack spacing={4} wrap="wrap">
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
              <Button
                colorScheme="teal"
                size="lg"
                onClick={onOpen}
                leftIcon={<FaFileAlt />}
                px={8}
                _hover={{ transform: 'translateY(-2px)', shadow: 'lg' }}
              >
                Read Whitepaper
              </Button>
            </HStack>
          </Stack>
          <Box
            display={{ base: 'none', md: 'block' }}
            maxW="500px"
            w="100%"
          >
            <Image
              src="/hero.png"
              alt="NeuroSpace AI"
              fallbackSrc="https://via.placeholder.com/500x400"
              rounded="lg"
              shadow="2xl"
            />
          </Box>
        </Stack>
      </Container>

      {/* Key Features Section */}
      <Box py={20} bg={useColorModeValue('white', 'gray.800')}>
        <Container maxW="container.xl">
          <VStack spacing={12}>
            <Stack spacing={4} textAlign="center">
              <Heading color={headingColor}>Verifiable AI Infrastructure</Heading>
              <Text fontSize="lg" color={textColor} maxW="600px">
                Every layer of NeuroSpace is designed to restore user agency, auditability, and credibility in AI interactions
              </Text>
            </Stack>

            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={10}>
              <Feature
                icon={FaRobot}
                title="Advanced AI Chat"
                text="Interact with state-of-the-art AI models for intelligent conversations"
              />
              <Feature
                icon={FaShieldAlt}
                title="Cryptographic Verification"
                text="Every interaction is hashed, signed, and stored on IPFS with blockchain commitment"
              />
              <Feature
                icon={FaDatabase}
                title="Verifiable RAG"
                text="Document-grounded AI responses with cryptographic guarantees and source verification"
              />
              <Feature
                icon={FaCoins}
                title="NeuroCoin (NSPACE)"
                text="Powered by a fixed-supply ERC-20 token for payments, staking, and governance"
              />
            </SimpleGrid>
          </VStack>
        </Container>
      </Box>

      {/* How It Works Section */}
      <Box py={20} bg={useColorModeValue('gray.50', 'gray.900')}>
        <Container maxW="container.xl">
          <VStack spacing={12}>
            <Stack spacing={4} textAlign="center">
              <Heading color={headingColor}>How It Works</Heading>
              <Text fontSize="lg" color={textColor} maxW="600px">
                NeuroSpace transforms every AI interaction into a verifiable, on-chain record using cryptography and decentralized storage.
              </Text>
            </Stack>

            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={10}>
              <HowItWorksStep
                step={1}
                icon={FaEdit}
                title="Ask a Question"
                text="Submit a prompt to a powerful LLM—anything from code to conversation."
              />
              <HowItWorksStep
                step={2}
                icon={FaMagic}
                title="Get a Response"
                text="The AI generates an answer, grounded in model config and optional documents."
              />
              <HowItWorksStep
                step={3}
                icon={FaKey}
                title="Cryptographic Signing"
                text="Prompt, response, and metadata are hashed and signed by your wallet."
              />
              <HowItWorksStep
                step={4}
                icon={FaLink}
                title="Verifiable Storage"
                text="We store the proof on IPFS and commit the hash on-chain—forever traceable."
              />
            </SimpleGrid>
          </VStack>
        </Container>
      </Box>

      {/* Value Proposition Section */}
      <Box py={20}>
        <Container maxW="container.xl">
          <Stack spacing={12}>
            <Stack spacing={4} textAlign="center">
              <Heading color={headingColor}>Why NeuroSpace Matters</Heading>
              <Text fontSize="lg" color={textColor} maxW="800px" mx="auto">
                In a world increasingly shaped by black-box models, NeuroSpace reimagines machine intelligence 
                as a publicly verifiable, user-controlled utility.
              </Text>
            </Stack>

            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={8}>
              <Stack
                p={8}
                bg={useColorModeValue('blue.50', 'blue.900')}
                rounded="xl"
                spacing={4}
              >
                <Icon as={FaCheckCircle} w={8} h={8} color={accentColor} />
                <Heading size="md">Transparent AI</Heading>
                <Text color={textColor}>
                  Every prompt and response is hashed using SHA-256 and signed with your Ethereum wallet, 
                  creating a tamper-proof record of every conversation.
                </Text>
              </Stack>

              <Stack
                p={8}
                bg={useColorModeValue('purple.50', 'purple.900')}
                rounded="xl"
                spacing={4}
              >
                <Icon as={FaShieldAlt} w={8} h={8} color={accentColor} />
                <Heading size="md">Public Auditing</Heading>
                <Text color={textColor}>
                  Anyone can verify the integrity of messages, identity of signers, and timestamps—no 
                  centralized authority required.
                </Text>
              </Stack>
            </SimpleGrid>
          </Stack>
        </Container>
      </Box>

      {/* Powered by NSPACE Section */}
      <Box py={20} bg={useColorModeValue('white', 'gray.800')}>
        <Container maxW="container.xl">
          <VStack spacing={10}>
            <Stack spacing={4} textAlign="center">
              <Heading color={headingColor}>Powered by NSPACE</Heading>
              <Text fontSize="lg" color={textColor} maxW="700px">
                NeuroCoin (NSPACE) is the utility token of NeuroSpace. It fuels chat interactions, RAG queries, staking, and governance—ensuring that the system remains decentralized, transparent, and community-aligned.
              </Text>
            </Stack>

            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={8}>
              <Feature
                icon={FaCoins}
                title="Payments"
                text="Use NSPACE to pay for model queries and document-grounded responses."
              />
              <Feature
                icon={FaShieldAlt}
                title="Staking"
                text="Stake NSPACE to prioritize interactions, support verifiers, or audit feedback."
              />
              <Feature
                icon={FaNetworkWired}
                title="Governance"
                text="Vote on supported models, moderation policy, and ecosystem direction."
              />
            </SimpleGrid>

            <Stack align="center" pt={6}>
              <Text color={textColor}>Fixed Supply: <strong>100,000,000 NSPACE</strong> &nbsp; • &nbsp; Network: <strong>Base L2</strong></Text>
              <Button colorScheme="blue" size="lg" mt={4}>
                Learn More
              </Button>
            </Stack>
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
                Ready to Experience Verifiable AI?
              </Heading>
              <Text fontSize="lg" color={textColor}>
                Join NeuroSpace today and be part of the future of transparent, trustworthy AI interactions
              </Text>
            </Stack>
            <Button
              colorScheme="blue"
              size="lg"
              onClick={() => navigate('/chat')}
              px={8}
              _hover={{ transform: 'translateY(-2px)', shadow: 'lg' }}
            >
              Get Started
            </Button>
          </Stack>
        </Container>
      </Box>

      {/* Whitepaper Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="md">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>NeuroSpace Whitepaper</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <Text>Choose how you'd like to view the whitepaper:</Text>
              <Button
                colorScheme="blue"
                leftIcon={<FaFileAlt />}
                onClick={() => window.open('/NeuroSpace_Whitepaper.pdf', '_blank')}
                w="full"
              >
                Open in New Tab
              </Button>
              <Button
                colorScheme="purple"
                leftIcon={<FaDownload />}
                onClick={() => {
                  const link = document.createElement('a');
                  link.href = '/NeuroSpace_Whitepaper.pdf';
                  link.download = 'NeuroSpace_Whitepaper.pdf';
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                }}
                w="full"
              >
                Download PDF
              </Button>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button colorScheme="blue" mr={3} onClick={onClose}>
              Close
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}

export default LandingPage 