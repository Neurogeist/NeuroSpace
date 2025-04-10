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

export default function Chat() {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [availableModels, setAvailableModels] = useState<{ [key: string]: string }>({});
    const [selectedModel, setSelectedModel] = useState<string>("mixtral-remote");
    const [isInitializing, setIsInitializing] = useState(true);
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
        const loadInitialData = async () => {
            try {
                setIsInitializing(true);
                const [models, sessions] = await Promise.all([
                    getAvailableModels(),
                    getSessions()
                ]);
                
                // Process sessions to ensure all messages have complete metadata
                const processedSessions = sessions.map(session => ({
                    ...session,
                    messages: session.messages.map(msg => ({
                        ...msg,
                        ipfsHash: msg.ipfsHash || undefined,
                        transactionHash: msg.transactionHash || undefined,
                        metadata: msg.metadata ? {
                            model: msg.metadata.model || selectedModel,
                            model_id: msg.metadata.model_id || '',
                            temperature: msg.metadata.temperature || 0.7,
                            max_tokens: msg.metadata.max_tokens || 512,
                            top_p: msg.metadata.top_p || 0.9,
                            do_sample: msg.metadata.do_sample ?? true,
                            num_beams: msg.metadata.num_beams || 1,
                            early_stopping: msg.metadata.early_stopping ?? false
                        } : {
                            model: selectedModel,
                            model_id: '',
                            temperature: 0.7,
                            max_tokens: 512,
                            top_p: 0.9,
                            do_sample: true,
                            num_beams: 1,
                            early_stopping: false
                        }
                    }))
                }));
                
                setAvailableModels(models);
                setSessions(processedSessions);
                
                if (activeSessionId) {
                    const session = await getSession(activeSessionId);
                    const processedMessages = session.messages.map(msg => ({
                        ...msg,
                        ipfsHash: msg.ipfsHash || undefined,
                        transactionHash: msg.transactionHash || undefined,
                        metadata: msg.metadata ? {
                            model: msg.metadata.model || selectedModel,
                            model_id: msg.metadata.model_id || '',
                            temperature: msg.metadata.temperature || 0.7,
                            max_tokens: msg.metadata.max_tokens || 512,
                            top_p: msg.metadata.top_p || 0.9,
                            do_sample: msg.metadata.do_sample ?? true,
                            num_beams: msg.metadata.num_beams || 1,
                            early_stopping: msg.metadata.early_stopping ?? false
                        } : {
                            model: selectedModel,
                            model_id: '',
                            temperature: 0.7,
                            max_tokens: 512,
                            top_p: 0.9,
                            do_sample: true,
                            num_beams: 1,
                            early_stopping: false
                        }
                    }));
                    setMessages(processedMessages);
                }
                
                // If no model is selected, set the first available model
                if (!selectedModel && Object.keys(models).length > 0) {
                    setSelectedModel(Object.keys(models)[0]);
                }
                
                setIsInitializing(false);
            } catch (err) {
                console.error('Error loading initial data:', err);
                setError(err instanceof Error ? err.message : 'Failed to load data');
                setIsInitializing(false);
            }
        };
        
        loadInitialData();
    }, []);

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
        const loadSession = async () => {
            if (activeSessionId) {
                try {
                    const session = await getSession(activeSessionId);
                    // Ensure metadata is properly structured
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
                }
            }
        };
        loadSession();
    }, [activeSessionId]);

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
            
            // Update active session if needed
            if (response.session_id && response.session_id !== activeSessionId) {
                setActiveSessionId(response.session_id);
                // Fetch updated sessions list
                const sessions = await getSessions();
                setSessions(sessions);
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
    };

    const handleSelectSession = async (sessionId: string) => {
        try {
            const session = await getSession(sessionId);
            console.log('Loaded session:', session);
            
            const messagesWithMetadata = session.messages.map(msg => {
                console.log('Processing message:', msg);
                const processedMessage = {
                    ...msg,
                    ipfsHash: msg.ipfsHash || undefined,
                    transactionHash: msg.transactionHash || undefined,
                    metadata: msg.metadata ? {
                        model: msg.metadata.model || selectedModel,
                        model_id: msg.metadata.model_id || '',
                        temperature: msg.metadata.temperature || 0.7,
                        max_tokens: msg.metadata.max_tokens || 512,
                        top_p: msg.metadata.top_p || 0.9,
                        do_sample: msg.metadata.do_sample ?? true,
                        num_beams: msg.metadata.num_beams || 1,
                        early_stopping: msg.metadata.early_stopping ?? false
                    } : {
                        model: selectedModel,
                        model_id: '',
                        temperature: 0.7,
                        max_tokens: 512,
                        top_p: 0.9,
                        do_sample: true,
                        num_beams: 1,
                        early_stopping: false
                    }
                };
                console.log('Processed message:', processedMessage);
                return processedMessage;
            });
            
            setMessages(messagesWithMetadata);
            setActiveSessionId(sessionId);
        } catch (err) {
            console.error('Error loading session:', err);
            setError(err instanceof Error ? err.message : 'Failed to load session');
        }
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
        const provider = name.includes('remote') ? 'Remote' : 'Local';
        if (!acc[provider]) {
            acc[provider] = [];
        }
        acc[provider].push({ name, id });
        return acc;
    }, {} as { [key: string]: { name: string; id: string }[] });

    if (isInitializing) {
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
                        sessions={sessions}
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