import React, { useState, useRef, useEffect } from 'react';
import {
    Box,
    VStack,
    HStack,
    Input,
    Button,
    Text,
    IconButton,
    useColorModeValue,
    Flex,
    Link,
    Tooltip,
    Container,
    Select,
    FormControl,
    FormLabel,
    UnorderedList,
    ListItem,
    Heading,
    useDisclosure,
    Collapse,
    Textarea,
    useBreakpointValue,
    Spinner,
    Alert,
    AlertIcon,
    AlertTitle,
    AlertDescription,
    useToast
} from '@chakra-ui/react';
import { FiSend, FiRefreshCw, FiHash, FiLink } from 'react-icons/fi';
import { ChevronLeftIcon, ChevronRightIcon } from '@chakra-ui/icons';
import { ChatMessage, ChatSession } from '../types/chat';
import { submitPrompt, getAvailableModels, getSessions, getSession } from '../services/api';
import Sidebar from './Sidebar';
import ChatMessageComponent from './ChatMessage';
import { useApp } from '../context/AppContext';

export default function Chat() {
    const { models: availableModels, sessions: availableSessions, isLoading, error, refreshSessions } = useApp();
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [activeSessionId, setActiveSessionId] = useState<string | null>(() => {
        // Try to get the active session from localStorage on initial load
        const savedSessionId = localStorage.getItem('activeSessionId');
        return savedSessionId || null;
    });
    const [selectedModel, setSelectedModel] = useState<string>(() => {
        // Try to get the selected model from localStorage on initial load
        const savedModel = localStorage.getItem('selectedModel');
        return savedModel || 'mixtral-8x7b-instruct';
    });
    const [isThinking, setIsThinking] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const { isOpen: isSidebarOpen, onToggle: toggleSidebar } = useDisclosure({ defaultIsOpen: true });
    const toast = useToast();

    const bgColor = useColorModeValue('gray.50', 'gray.900');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const messageBgColor = useColorModeValue('gray.50', 'gray.700');
    const userMessageBgColor = useColorModeValue('blue.50', 'blue.900');
    const textColor = useColorModeValue('gray.800', 'gray.200');
    const linkColor = useColorModeValue('blue.500', 'blue.300');
    const inputBgColor = useColorModeValue('white', 'gray.800');
    const inputBorderColor = useColorModeValue('gray.200', 'gray.600');
    const inputTextColor = useColorModeValue('gray.800', 'gray.200');
    const placeholderColor = useColorModeValue('gray.500', 'gray.400');
    const timestampColor = useColorModeValue('gray.500', 'gray.400');
    const buttonBgColor = useColorModeValue('blue.500', 'blue.400');
    const buttonHoverBgColor = useColorModeValue('blue.600', 'blue.500');

    const sidebarWidth = useBreakpointValue({ base: '100%', md: '300px' });
    const mainContentWidth = useBreakpointValue({ base: '100%', md: 'calc(100% - 300px)' });
    const maxMessageWidth = useBreakpointValue({ base: '100%', md: '800px' });

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto';
            inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 150)}px`;
        }
    }, [input]);

    useEffect(() => {
        // This effect now runs *only* when availableSessions changes.
        // If, at the time the sessions list updates, there's no active session,
        // it selects the first one as a default.
        // It will NOT run when handleNewChat sets activeSessionId to null.
        if (availableSessions.length > 0 && !activeSessionId) {
             console.log("Setting default session because availableSessions updated and no active session found.");
            setActiveSessionId(availableSessions[0].session_id);
        }
        // Remove activeSessionId from the dependency array
    }, [availableSessions]); // <-- Corrected dependency

    useEffect(() => {
        const loadSession = async () => {
            if (!activeSessionId) {
                setMessages([]);
                return;
            }

            try {
                const session = await getSession(activeSessionId);
                const messages = session.messages.map(msg => ({
                    ...msg,
                    metadata: {
                        ...msg.metadata,
                        verification_hash: msg.metadata?.verification_hash || msg.verification_hash,
                        signature: msg.metadata?.signature || msg.signature,
                        ipfs_cid: msg.metadata?.ipfs_cid || msg.ipfsHash,
                        transaction_hash: msg.metadata?.transaction_hash || msg.transactionHash
                    }
                }));
                setMessages(messages);
            } catch (error) {
                console.error('Error loading session:', error);
                toast({
                    title: "Error",
                    description: "Failed to load session. Please try again.",
                    status: "error",
                    duration: 3000,
                    isClosable: true,
                });
            }
        };

        loadSession();
    }, [activeSessionId]);

    useEffect(() => {
        if (activeSessionId) {
            localStorage.setItem('activeSessionId', activeSessionId);
        } else {
            localStorage.removeItem('activeSessionId');
        }
    }, [activeSessionId]);

    useEffect(() => {
        localStorage.setItem('selectedModel', selectedModel);
    }, [selectedModel]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isThinking) return;

        // Ensure a model is selected
        if (!selectedModel) {
            toast({
                title: "Error",
                description: "Please select a model before submitting",
                status: "error",
                duration: 3000,
                isClosable: true,
            });
            return;
        }

        // Add user message immediately
        const userMessage: ChatMessage = {
            content: input,
            role: 'user',
            timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        
        // Show thinking indicator
        setIsThinking(true);

        try {
            const response = await submitPrompt(input, selectedModel, activeSessionId || undefined);
            console.log('Prompt response:', response);

            const assistantMessage: ChatMessage = {
                content: response.response,
                role: 'assistant',
                timestamp: new Date().toISOString(),
                metadata: {
                    model: selectedModel,
                    model_id: response.model_id,
                    temperature: response.metadata.temperature,
                    max_tokens: response.metadata.max_tokens,
                    top_p: response.metadata.top_p,
                    do_sample: response.metadata.do_sample,
                    num_beams: response.metadata.num_beams,
                    early_stopping: response.metadata.early_stopping,
                    verification_hash: response.metadata.verification_hash,
                    signature: response.metadata.signature,
                    ipfs_cid: response.metadata.ipfs_cid,
                    transaction_hash: response.metadata.transaction_hash,
                },
                ipfsHash: response.metadata.ipfs_cid,
                transactionHash: response.metadata.transaction_hash,
            };

            setMessages(prev => [...prev, assistantMessage]);
            
            // Always refresh sessions after a successful response
            await refreshSessions();
            
            // Update active session if needed
            if (response.session_id) {
                setActiveSessionId(response.session_id);
                localStorage.setItem('activeSessionId', response.session_id);
            }
            
        } catch (error) {
            console.error('Error submitting prompt:', error);
            toast({
                title: "Error",
                description: "Failed to submit prompt. Please try again.",
                status: "error",
                duration: 3000,
                isClosable: true,
            });
        } finally {
            setIsThinking(false);
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setActiveSessionId(null);
        localStorage.removeItem('activeSessionId');
    };

    const handleSelectSession = async (sessionId: string) => {
        setActiveSessionId(sessionId);
    };

    const formatHash = (hash: string) => {
        return `${hash.slice(0, 6)}...${hash.slice(-4)}`;
    };

    const renderMetadata = (message: ChatMessage) => {
        if (!message.metadata) return null;

        return (
            <Box mt={2} fontSize="xs" color={timestampColor}>
                <HStack spacing={2}>
                    <Text>Model: {message.metadata.model}</Text>
                    <Text>•</Text>
                    <Text>Temperature: {message.metadata.temperature}</Text>
                    <Text>•</Text>
                    <Text>Max Tokens: {message.metadata.max_tokens}</Text>
                </HStack>
            </Box>
        );
    };

    const groupedModels = Object.entries(availableModels).reduce((acc, [name, id]) => {
        const provider = name.includes('local') ? 'Local' : 'Remote';
        if (!acc[provider]) {
            acc[provider] = [];
        }
        acc[provider].push({ name, id });
        return acc;
    }, {} as { [key: string]: { name: string; id: string }[] });

    if (isLoading) {
        return (
            <Flex h="100vh" align="center" justify="center" bg={bgColor}>
                <VStack spacing={4}>
                    <Spinner size="xl" color="blue.500" />
                    <Text>Loading chat interface...</Text>
                </VStack>
            </Flex>
        );
    }

    return (
        <Flex h="100vh" bg={bgColor} position="relative">
            <IconButton
                aria-label="Toggle sidebar"
                icon={isSidebarOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
                onClick={toggleSidebar}
                position="absolute"
                left={isSidebarOpen ? "300px" : "0"}
                top="50%"
                transform="translateY(-50%)"
                zIndex={2}
                bg={inputBgColor}
                _hover={{ bg: buttonHoverBgColor }}
                transition="all 0.2s"
            />

            <Collapse in={isSidebarOpen} animateOpacity>
                <Box
                    w={sidebarWidth}
                    h="100%"
                    borderRight="1px"
                    borderColor={borderColor}
                    bg={inputBgColor}
                    position="relative"
                    zIndex={1}
                >
                    <Sidebar
                    sessions={availableSessions}
                        activeSessionId={activeSessionId}
                        onNewChat={handleNewChat}
                        onSelectSession={handleSelectSession}
                    />
                </Box>
            </Collapse>

            <Flex direction="column" flex="1" w={isSidebarOpen ? mainContentWidth : '100%'} transition="all 0.2s">
                <Box p={4} borderBottom="1px" borderColor={borderColor} bg={inputBgColor}>
                    <Container maxW={maxMessageWidth}>
                        <HStack justify="space-between" align="center">
                            <Text fontSize="2xl" fontWeight="bold" color={textColor}>
                                NeuroChain Chat
                            </Text>
                            <FormControl width="auto">
                                <Select
                                    value={selectedModel}
                                    onChange={(e) => setSelectedModel(e.target.value)}
                                    size="md"
                                    bg={inputBgColor}
                                    borderColor={inputBorderColor}
                                    color={inputTextColor}
                                >
                                    {Object.entries(groupedModels).map(([provider, models]) => (
                                        <optgroup key={provider} label={provider}>
                                            {models.map(({ name }) => (
                                                <option key={name} value={name}>
                                                    {name}
                                                </option>
                                            ))}
                                        </optgroup>
                                    ))}
                                </Select>
                            </FormControl>
                        </HStack>
                    </Container>
                </Box>

                {error && (
                    <Alert status="error" mb={4}>
                        <AlertIcon />
                        <AlertTitle>Error:</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                <Flex direction="column" flex="1" overflowY="auto" p={4}>
                    <Container maxW={maxMessageWidth}>
                        <VStack spacing={4} align="stretch">
                            {messages.map((message, index) => (
                                <ChatMessageComponent key={index} message={message} />
                            ))}
                            {isThinking && (
                                <Box p={4} borderRadius="lg" bg={messageBgColor} maxW="80%" alignSelf="flex-start">
                                    <HStack>
                                        <Spinner size="sm" />
                                        <Text>Thinking...</Text>
                                    </HStack>
                                </Box>
                            )}
                            <div ref={messagesEndRef} />
                        </VStack>
                    </Container>
                </Flex>

                <Box p={4} borderTop="1px" borderColor={borderColor} bg={inputBgColor}>
                    <Container maxW={maxMessageWidth}>
                        <form onSubmit={handleSubmit}>
                            <HStack>
                                <FormControl>
                                    <Textarea
                                        ref={inputRef}
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        placeholder="Type your message..."
                                        size="md"
                                        resize="none"
                                        minH="40px"
                                        maxH="150px"
                                        overflowY="auto"
                                        bg={inputBgColor}
                                        borderColor={inputBorderColor}
                                        color={inputTextColor}
                                        _hover={{ borderColor: buttonBgColor }}
                                        _focus={{ borderColor: buttonBgColor, boxShadow: 'none' }}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter' && !e.shiftKey) {
                                                e.preventDefault();
                                                handleSubmit(e);
                                            }
                                        }}
                                    />
                                </FormControl>
                                <Button
                                    type="submit"
                                    colorScheme="blue"
                                    isLoading={isThinking}
                                    isDisabled={!input.trim()}
                                    px={6}
                                >
                                    Send
                                </Button>
                            </HStack>
                        </form>
                    </Container>
                </Box>
            </Flex>
        </Flex>
    );
} 