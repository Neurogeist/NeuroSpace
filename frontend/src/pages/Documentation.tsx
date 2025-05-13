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
} from '@chakra-ui/react'
import { FaBook, FaRocket, FaShieldAlt, FaDatabase, FaFileAlt, FaCheckCircle, FaWallet, FaRobot, FaLock, FaLink } from 'react-icons/fa'
import { Link as RouterLink } from 'react-router-dom'

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

          {/* How It Works */}
          <Section title="How It Works (Technical Overview)" icon={FaBook}>
            <VStack align="stretch" spacing={4}>
              <Box>
                <Heading size="sm" mb={2}>Architecture Summary</Heading>
                <List spacing={2}>
                  <ListItem>
                    <ListIcon as={FaLock} color="blue.500" />
                    Cryptographic hashing of all interactions.
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaWallet} color="blue.500" />
                    Ethereum wallet signing for message verification.
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaDatabase} color="blue.500" />
                    IPFS for decentralized storage of interactions.
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaLink} color="blue.500" />
                    Smart contracts for on-chain commitments.
                  </ListItem>
                </List>
              </Box>

              <Box>
                <Heading size="sm" mb={2}>Verifiability Flow</Heading>
                <List spacing={2}>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    User signs a message with their wallet.
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    Message gets hashed (SHA-256) and stored on IPFS.
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    Hash committed to blockchain (for paid messages).
                  </ListItem>
                </List>
              </Box>
            </VStack>
          </Section>

          {/* Whitepaper Callout */}
          <Section title="Whitepaper" icon={FaFileAlt}>
            <VStack align="stretch" spacing={4}>
              <Text color={textColor}>
                For a detailed technical and tokenomics breakdown, view the NeuroSpace whitepaper.
              </Text>
              <Button colorScheme="blue" leftIcon={<FaFileAlt />} onClick={onOpen}>
                View Whitepaper
              </Button>
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
