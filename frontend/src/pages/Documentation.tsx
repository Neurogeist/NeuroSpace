import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Stack,
  Link,
  List,
  ListItem,
  ListIcon,
  useColorModeValue,
  Icon,
  Button,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  SimpleGrid,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
} from '@chakra-ui/react'
import { FaRocket, FaShieldAlt, FaDatabase, FaFileAlt, FaCheckCircle, FaWallet, FaRobot, FaLock, FaLink, FaQuestionCircle, FaCode, FaThumbsUp, FaVoteYea, FaCoins, FaExclamationTriangle, FaStar, FaLightbulb } from 'react-icons/fa'

const Section = ({ title, icon, children }: { title: string; icon: any; children: React.ReactNode }) => {
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  return (
    <Box
      bg={bgColor}
      p={6}
      rounded="xl"
      shadow="md"
      borderWidth="1px"
      borderColor={borderColor}
    >
      <HStack spacing={4} mb={4}>
        <Icon as={icon} w={6} h={6} color="blue.500" />
        <Heading size="md">{title}</Heading>
      </HStack>
      {children}
    </Box>
  )
}

const Documentation = () => {
  const bgColor = useColorModeValue('gray.50', 'gray.900')
  const textColor = useColorModeValue('gray.600', 'gray.400')
  const headingColor = useColorModeValue('gray.800', 'white')
  const { isOpen, onOpen, onClose } = useDisclosure()

  return (
    <Box bg={bgColor} minH="100vh" py={10}>
      <Container maxW="container.xl">
        <VStack spacing={8} align="stretch">
          {/* Page Header */}
          <Stack spacing={4}>
            <Heading color={headingColor}>NeuroSpace Documentation</Heading>
            <Text fontSize="lg" color={textColor}>
              Everything you need to know to get started and understand how NeuroSpace works.
            </Text>
            <Button colorScheme="blue" leftIcon={<FaFileAlt />} onClick={onOpen}>
              Read the Whitepaper
            </Button>
          </Stack>

          {/* Quick Start */}
          <Section title="Getting Started" icon={FaRocket}>
            <VStack align="stretch" spacing={4}>
              <Text color={textColor}>
                NeuroSpace lets you interact with AI verifiably. You can start for free or choose to pay using ETH or NeuroCoin.
              </Text>

              <Box>
                <Heading size="sm" mb={2}>Option 1: Free Usage (Best for New Users)</Heading>
                <List spacing={2}>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    Connect your wallet.
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    Enjoy <strong>10 free messages</strong>. No gas, no tokens needed.
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    Free messages are off-chain (not stored on blockchain).
                  </ListItem>
                </List>
              </Box>

              <Box>
                <Heading size="sm" mb={2}>Option 2: Pay with ETH</Heading>
                <List spacing={2}>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    Connect MetaMask or compatible wallet.
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    Make sure you have ETH on <strong>Base Network</strong>.{' '}
                    <Link href="https://bridge.base.org" color="blue.500" isExternal>
                      Bridge ETH here.
                    </Link>
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    Pay per message directly in the app.
                  </ListItem>
                </List>
              </Box>

              <Box>
                <Heading size="sm" mb={2}>Option 3: Pay with NeuroCoin (Coming Soon)</Heading>
                <List spacing={2}>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    Buy NeuroCoin (soon on Uniswap Base).
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    Approve NeuroCoin in the app.
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    Pay per message using NeuroCoin (no ETH needed).
                  </ListItem>
                </List>
              </Box>
            </VStack>
          </Section>

          {/* Overview Section */}
          <Section title="What is NeuroSpace?" icon={FaQuestionCircle}>
            <VStack align="stretch" spacing={4}>
              <Text color={textColor}>
                NeuroSpace is a decentralized protocol for verifiable AI that makes AI outputs transparent, 
                traceable, and tamper-evident through a combination of blockchain technology and cryptographic proofs.
              </Text>
              
              <Box>
                <Heading size="sm" mb={2}>Core Components</Heading>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaLock} color="blue.500" />
                      <Text fontWeight="bold">Cryptographic Security</Text>
                    </HStack>
                    <Text fontSize="sm">SHA-256 hashing for message integrity</Text>
                  </Box>
                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaWallet} color="blue.500" />
                      <Text fontWeight="bold">Wallet Signatures</Text>
                    </HStack>
                    <Text fontSize="sm">EIP-191 compatible Ethereum signatures</Text>
                  </Box>
                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaDatabase} color="blue.500" />
                      <Text fontWeight="bold">Decentralized Storage</Text>
                    </HStack>
                    <Text fontSize="sm">IPFS for content persistence</Text>
                  </Box>
                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaLink} color="blue.500" />
                      <Text fontWeight="bold">Smart Contracts</Text>
                    </HStack>
                    <Text fontSize="sm">Base chain commitments</Text>
                  </Box>
                </SimpleGrid>
              </Box>
            </VStack>
          </Section>

          {/* Problems We Solve Section */}
          <Section title="Problems We Solve" icon={FaShieldAlt}>
            <VStack align="stretch" spacing={6}>
              <Box p={4} borderWidth="1px" borderRadius="lg">
                <Heading size="sm" mb={2}>1. Opaque, Black-Box AI Systems</Heading>
                <Text color={textColor}>
                  Today's AI platforms hide the models, infrastructure, and parameters behind closed APIs. 
                  Users have no way to inspect, verify, or audit how answers are generated—or by whom. 
                  NeuroSpace replaces this with fully transparent, verifiable, and auditable AI outputs 
                  where every detail is open and provable.
                </Text>
              </Box>

              <Box p={4} borderWidth="1px" borderRadius="lg">
                <Heading size="sm" mb={2}>2. Zero Accountability for AI Outputs</Heading>
                <Text color={textColor}>
                  When an AI makes a mistake, spreads misinformation, or behaves badly, there's no way to 
                  prove what happened—or who's responsible. NeuroSpace creates immutable, on-chain records 
                  tied to cryptographically provable wallet signatures, ensuring every response is 
                  attributable and accountable.
                </Text>
              </Box>

              <Box p={4} borderWidth="1px" borderRadius="lg">
                <Heading size="sm" mb={2}>3. Unverifiable Document Sources (RAG)</Heading>
                <Text color={textColor}>
                  Most Retrieval-Augmented Generation (RAG) systems give you citations you can't trust. 
                  Documents might change, disappear, or be misrepresented. NeuroSpace makes every source 
                  document immutable and traceable on IPFS, guaranteeing that citations are real, fixed, 
                  and tamper-proof.
                </Text>
              </Box>

              <Box p={4} borderWidth="1px" borderRadius="lg">
                <Heading size="sm" mb={2}>4. Invisible Agent Reasoning and Conversations</Heading>
                <Text color={textColor}>
                  Complex AI agents and chat sessions often perform multi-step reasoning—but there's no 
                  way to see their thought process. NeuroSpace introduces verifiable session and agent 
                  traceability, where every step, tool call, and action is logged, signed, and stored, 
                  creating a complete audit trail.
                </Text>
              </Box>

              <Box p={4} borderWidth="1px" borderRadius="lg">
                <Heading size="sm" mb={2}>5. Closed, Centralized Model Evaluation Systems</Heading>
                <Text color={textColor}>
                  Model evaluation today is siloed and controlled by the same companies running the models. 
                  NeuroSpace opens the door to community-driven, transparent model benchmarking and feedback 
                  systems, enabling truly open AI reputation markets, leaderboards, and decentralized model alignment.
                </Text>
              </Box>
            </VStack>
          </Section>

          {/* Traditional AI Problems Section */}
          <Section title="The Problem with Traditional AI Platforms" icon={FaExclamationTriangle}>
            <VStack align="stretch" spacing={4}>
              <Alert status="warning" variant="subtle" borderRadius="md">
                <AlertIcon />
                <Box>
                  <AlertTitle>Closed Black Boxes</AlertTitle>
                  <AlertDescription>
                    Most AI platforms today operate as closed systems where trust is entirely dependent on the platform operator.
                  </AlertDescription>
                </Box>
              </Alert>

              <List spacing={3}>
                <ListItem>
                  <ListIcon as={FaExclamationTriangle} color="orange.500" />
                  <strong>Hidden Configuration:</strong> You can't see how the model was configured
                </ListItem>
                <ListItem>
                  <ListIcon as={FaExclamationTriangle} color="orange.500" />
                  <strong>No Audit Trail:</strong> You can't verify response sources or integrity
                </ListItem>
                <ListItem>
                  <ListIcon as={FaExclamationTriangle} color="orange.500" />
                  <strong>Opaque Processing:</strong> No insight into data processing or tool usage
                </ListItem>
                <ListItem>
                  <ListIcon as={FaExclamationTriangle} color="orange.500" />
                  <strong>Blind Trust:</strong> Forced to trust providers without proof or accountability
                </ListItem>
              </List>
            </VStack>
          </Section>

          {/* Trust-First AI Section */}
          <Section title="How NeuroSpace is Different" icon={FaStar}>
            <VStack align="stretch" spacing={4}>
              <Text color={textColor} fontSize="lg" fontWeight="medium">
                We're building the first fully decentralized, verifiable AI platform where trust is built into the protocol itself.
              </Text>

              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <Box p={4} borderWidth="1px" borderRadius="lg" bg={useColorModeValue('blue.50', 'blue.900')}>
                  <HStack mb={2}>
                    <Icon as={FaLock} color="blue.500" />
                    <Text fontWeight="bold">Complete Transparency</Text>
                  </HStack>
                  <Text fontSize="sm">Every interaction is hashed, signed, stored on IPFS, and committed on-chain</Text>
                </Box>
                <Box p={4} borderWidth="1px" borderRadius="lg" bg={useColorModeValue('blue.50', 'blue.900')}>
                  <HStack mb={2}>
                    <Icon as={FaShieldAlt} color="blue.500" />
                    <Text fontWeight="bold">Public Parameters</Text>
                  </HStack>
                  <Text fontSize="sm">Model parameters, session metadata, and document sources are fully public and tamper-evident</Text>
                </Box>
                <Box p={4} borderWidth="1px" borderRadius="lg" bg={useColorModeValue('blue.50', 'blue.900')}>
                  <HStack mb={2}>
                    <Icon as={FaWallet} color="blue.500" />
                    <Text fontWeight="bold">User Control</Text>
                  </HStack>
                  <Text fontSize="sm">Users, not providers, control the conversation, the data, and the proofs</Text>
                </Box>
                <Box p={4} borderWidth="1px" borderRadius="lg" bg={useColorModeValue('blue.50', 'blue.900')}>
                  <HStack mb={2}>
                    <Icon as={FaLink} color="blue.500" />
                    <Text fontWeight="bold">Transparent Infrastructure</Text>
                  </HStack>
                  <Text fontSize="sm">All API interactions and infrastructure components are verifiable and auditable</Text>
                </Box>
              </SimpleGrid>
            </VStack>
          </Section>

          {/* Future Vision Section */}
          <Section title="The Future We Can Build Together" icon={FaLightbulb}>
            <VStack align="stretch" spacing={4}>
              <Text color={textColor}>
                NeuroSpace is more than a chat app—it's the foundation for the next generation of transparent, 
                accountable AI infrastructure.
              </Text>

              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <Box p={4} borderWidth="1px" borderRadius="lg">
                  <HStack mb={2}>
                    <Icon as={FaCheckCircle} color="green.500" />
                    <Text fontWeight="bold">Verifiable Model Benchmarking</Text>
                  </HStack>
                  <Text fontSize="sm">Compare models in a fully auditable, tamper-proof way</Text>
                </Box>
                <Box p={4} borderWidth="1px" borderRadius="lg">
                  <HStack mb={2}>
                    <Icon as={FaVoteYea} color="green.500" />
                    <Text fontWeight="bold">Open Model Evaluation</Text>
                  </HStack>
                  <Text fontSize="sm">Build trustless leaderboards and feedback systems</Text>
                </Box>
                <Box p={4} borderWidth="1px" borderRadius="lg">
                  <HStack mb={2}>
                    <Icon as={FaShieldAlt} color="green.500" />
                    <Text fontWeight="bold">Decentralized AI Governance</Text>
                  </HStack>
                  <Text fontSize="sm">Protocol-driven moderation and model alignment</Text>
                </Box>
                <Box p={4} borderWidth="1px" borderRadius="lg">
                  <HStack mb={2}>
                    <Icon as={FaRobot} color="green.500" />
                    <Text fontWeight="bold">Agent Traceability</Text>
                  </HStack>
                  <Text fontSize="sm">Transparent multi-step reasoning and execution traces</Text>
                </Box>
              </SimpleGrid>

              <Box mt={4} p={4} borderWidth="1px" borderRadius="lg" bg={useColorModeValue('green.50', 'green.900')}>
                <Text fontWeight="bold" color={useColorModeValue('green.800', 'green.100')}>
                  This is the beginning of provable AI for everyone—not just companies, but communities, 
                  regulators, and users around the world.
                </Text>
              </Box>
            </VStack>
          </Section>

          {/* Technical Deep Dive */}
          <Section title="Technical Deep Dive" icon={FaCode}>
            <VStack align="stretch" spacing={6}>
              <Box>
                <Heading size="sm" mb={2}>Verifiability Process</Heading>
                <VStack align="stretch" spacing={4}>
                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaFileAlt} color="blue.500" />
                      <Text fontWeight="bold">1. Message Serialization</Text>
                    </HStack>
                    <Text fontSize="sm">Every prompt, response, and metadata is converted into a deterministic object format.</Text>
                  </Box>
                  
                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaLock} color="blue.500" />
                      <Text fontWeight="bold">2. Hash Generation</Text>
                    </HStack>
                    <Text fontSize="sm">The serialized object is hashed using SHA-256 to create a unique fingerprint.</Text>
                  </Box>

                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaWallet} color="blue.500" />
                      <Text fontWeight="bold">3. Wallet Signing</Text>
                    </HStack>
                    <Text fontSize="sm">Users sign the hash with their Ethereum wallet (EIP-191 compatible).</Text>
                  </Box>

                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaLink} color="blue.500" />
                      <Text fontWeight="bold">4. On-Chain Commitment</Text>
                    </HStack>
                    <Text fontSize="sm">The signature and hash are submitted to the NeuroSpace smart contract on Base chain.</Text>
                  </Box>

                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaDatabase} color="blue.500" />
                      <Text fontWeight="bold">5. IPFS Storage</Text>
                    </HStack>
                    <Text fontSize="sm">Full content is stored on IPFS, referenced by Content Identifier (CID).</Text>
                  </Box>
                </VStack>
              </Box>

              <Box>
                <Heading size="sm" mb={2}>Key Guarantees</Heading>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaLock} color="blue.500" />
                      <Text fontWeight="bold">Integrity</Text>
                    </HStack>
                    <Text fontSize="sm">Messages cannot be forged without breaking their hash</Text>
                  </Box>
                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaShieldAlt} color="blue.500" />
                      <Text fontWeight="bold">Non-repudiation</Text>
                    </HStack>
                    <Text fontSize="sm">Authors cannot deny their messages due to signed hashes</Text>
                  </Box>
                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaDatabase} color="blue.500" />
                      <Text fontWeight="bold">Immutability</Text>
                    </HStack>
                    <Text fontSize="sm">On-chain records cannot be deleted or altered</Text>
                  </Box>
                  <Box p={4} borderWidth="1px" borderRadius="lg">
                    <HStack mb={2}>
                      <Icon as={FaShieldAlt} color="blue.500" />
                      <Text fontWeight="bold">Censorship Resistance</Text>
                    </HStack>
                    <Text fontSize="sm">Content remains accessible through IPFS</Text>
                  </Box>
                </SimpleGrid>
              </Box>
            </VStack>
          </Section>

          {/* Decentralized Feedback Section */}
          <Section title="Decentralized Feedback & Reputation" icon={FaThumbsUp}>
            <VStack align="stretch" spacing={4}>
              <Text color={textColor}>
                NeuroSpace implements a decentralized feedback system that allows the community to participate in 
                model quality assessment and protocol governance.
              </Text>

              <Box>
                <Heading size="sm" mb={2}>Feedback Mechanisms</Heading>
                <List spacing={2}>
                  <ListItem>
                    <ListIcon as={FaThumbsUp} color="blue.500" />
                    <strong>Quality Ratings:</strong> Users can rate AI responses based on accuracy and relevance
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaVoteYea} color="blue.500" />
                    <strong>Community Voting:</strong> Stakeholders participate in model quality assessment
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCoins} color="blue.500" />
                    <strong>Staking Rewards:</strong> Earn rewards for providing valuable feedback
                  </ListItem>
                </List>
              </Box>

              <Box>
                <Heading size="sm" mb={2}>Reputation System</Heading>
                <List spacing={2}>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    <strong>Feedback Weight:</strong> Reputation score influences voting power
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    <strong>Staking Tiers:</strong> Higher stakes provide greater influence
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    <strong>Quality Metrics:</strong> Track model performance over time
                  </ListItem>
                </List>
              </Box>
            </VStack>
          </Section>
        </VStack>
      </Container>

      {/* Whitepaper Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="full">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>NeuroSpace Whitepaper</ModalHeader>
          <ModalCloseButton />
          <ModalBody p={0}>
            <iframe
              src="/NeuroSpace_Whitepaper.pdf"
              style={{ width: '100%', height: '100vh', border: 'none' }}
              title="NeuroSpace Whitepaper"
            />
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

export default Documentation
