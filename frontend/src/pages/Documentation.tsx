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
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Divider,
  Icon,
  Button,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter
} from '@chakra-ui/react'
import { FaBook, FaRocket, FaShieldAlt, FaDatabase, FaFileAlt, FaCheckCircle, FaWallet, FaRobot, FaLock, FaLink, FaDownload } from 'react-icons/fa'
import { Link as RouterLink } from 'react-router-dom'
import { useState } from 'react'

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
          <Stack spacing={4}>
            <Heading color={headingColor}>Documentation</Heading>
            <Text fontSize="lg" color={textColor}>
              Learn about NeuroSpace's architecture, features, and how to get started.
            </Text>
          </Stack>

          {/* Overview Section */}
          <Section title="Overview" icon={FaBook}>
            <VStack align="stretch" spacing={4}>
              <Box>
                <Heading size="sm" mb={2}>What is NeuroSpace?</Heading>
                <Text color={textColor}>
                  NeuroSpace is a verifiable AI platform that combines advanced language models with blockchain technology.
                  It ensures transparency and trust in AI interactions through cryptographic verification and decentralized storage.
                </Text>
              </Box>
              
              <Box>
                <Heading size="sm" mb={2}>What problems does it solve?</Heading>
                <List spacing={2}>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    <Text as="span" color={textColor}>Black-box AI interactions</Text>
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    <Text as="span" color={textColor}>Lack of auditability in AI responses</Text>
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    <Text as="span" color={textColor}>Centralized control of AI systems</Text>
                  </ListItem>
                </List>
              </Box>

              <Box>
                <Heading size="sm" mb={2}>Architecture Summary</Heading>
                <List spacing={2}>
                  <ListItem>
                    <ListIcon as={FaLock} color="blue.500" />
                    <Text as="span" color={textColor}>Cryptographic hashing of all interactions</Text>
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaWallet} color="blue.500" />
                    <Text as="span" color={textColor}>Ethereum wallet signing for verification</Text>
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaDatabase} color="blue.500" />
                    <Text as="span" color={textColor}>IPFS for decentralized storage</Text>
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaLink} color="blue.500" />
                    <Text as="span" color={textColor}>Smart contracts for on-chain commitments</Text>
                  </ListItem>
                </List>
              </Box>
            </VStack>
          </Section>

          {/* Getting Started Section */}
          <Section title="Getting Started" icon={FaRocket}>
            <VStack align="stretch" spacing={4}>
              <Box>
                <Heading size="sm" mb={2}>Requirements</Heading>
                <List spacing={2}>
                  <ListItem>
                    <ListIcon as={FaWallet} color="blue.500" />
                    <Text as="span" color={textColor}>MetaMask or compatible Ethereum wallet</Text>
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaRobot} color="blue.500" />
                    <Text as="span" color={textColor}>Web3-enabled browser</Text>
                  </ListItem>
                </List>
              </Box>

              <Box>
                <Heading size="sm" mb={2}>How to Try</Heading>
                <List spacing={2}>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    <Text as="span" color={textColor}>
                      <Link as={RouterLink} to="/chat" color="blue.500">Chat</Link> - Connect your wallet and start chatting
                    </Text>
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    <Text as="span" color={textColor}>
                      <Link as={RouterLink} to="/rag" color="blue.500">RAG</Link> - Upload documents and ask questions
                    </Text>
                  </ListItem>
                </List>
              </Box>
            </VStack>
          </Section>

          {/* Verifiability Section */}
          <Section title="Verifiability" icon={FaShieldAlt}>
            <VStack align="stretch" spacing={4}>
              <Box>
                <Heading size="sm" mb={2}>Message Signing</Heading>
                <Text color={textColor}>
                  Every interaction is signed using your Ethereum wallet's private key. This creates a cryptographic proof
                  that you were the originator of the message.
                </Text>
              </Box>

              <Box>
                <Heading size="sm" mb={2}>Hash Computation</Heading>
                <Text color={textColor}>
                  Messages are hashed using SHA-256, creating a unique fingerprint of the content. This hash is then
                  signed to create a verifiable proof of authenticity.
                </Text>
              </Box>

              <Box>
                <Heading size="sm" mb={2}>Verification Process</Heading>
                <List spacing={2}>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    <Text as="span" color={textColor}>Retrieve the message hash from IPFS</Text>
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    <Text as="span" color={textColor}>Verify the signature using the signer's public key</Text>
                  </ListItem>
                  <ListItem>
                    <ListIcon as={FaCheckCircle} color="blue.500" />
                    <Text as="span" color={textColor}>Confirm the message hasn't been tampered with</Text>
                  </ListItem>
                </List>
              </Box>
            </VStack>
          </Section>

          {/* IPFS & On-Chain Storage Section */}
          <Section title="IPFS & On-Chain Storage" icon={FaDatabase}>
            <VStack align="stretch" spacing={4}>
              <Box>
                <Heading size="sm" mb={2}>Content Storage</Heading>
                <Text color={textColor}>
                  All interactions are stored on IPFS, providing decentralized and permanent storage. The IPFS Content
                  Identifier (CID) is then committed to the blockchain for additional security.
                </Text>
              </Box>

              <Box>
                <Heading size="sm" mb={2}>Example</Heading>
                <Text color={textColor}>
                  CID: <code>QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco</code>
                </Text>
                <Text color={textColor} mt={2}>
                  Smart Contract: <code>0x1234...5678</code>
                </Text>
              </Box>
            </VStack>
          </Section>

          {/* Whitepaper Section */}
          <Section title="Whitepaper" icon={FaFileAlt}>
            <VStack align="stretch" spacing={4}>
              <Text color={textColor}>
                For a detailed technical overview of NeuroSpace's architecture and tokenomics, please refer to our whitepaper.
              </Text>
              <Button
                colorScheme="blue"
                leftIcon={<FaFileAlt />}
                onClick={onOpen}
              >
                View Whitepaper
              </Button>
            </VStack>
          </Section>
        </VStack>
      </Container>

      {/* Whitepaper Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="full">
        <ModalOverlay />
        <ModalContent 
          w="100vw"
          h="100vh"
          m={0}
          p={0}
          display="flex"
          flexDirection="column"
        >
          <ModalHeader 
            py={2} 
            px={4}
            bg={useColorModeValue('white', 'gray.800')}
            borderBottomWidth="1px"
            borderColor={useColorModeValue('gray.200', 'gray.700')}
          >
            NeuroSpace Whitepaper
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody 
            p={0} 
            flex="1"
            position="relative"
            h="calc(100vh - 120px)"
          >
            <iframe
              src="/NeuroSpace_Whitepaper.pdf"
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                border: 'none'
              }}
              title="NeuroSpace Whitepaper"
            />
          </ModalBody>
          <ModalFooter 
            py={2}
            px={4}
            bg={useColorModeValue('white', 'gray.800')}
            borderTopWidth="1px"
            borderColor={useColorModeValue('gray.200', 'gray.700')}
          >
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