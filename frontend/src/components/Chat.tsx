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
    AlertDescription
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
    const [isLoading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [availableModels, setAvailableModels] = useState<{ [key: string]: string }>({});
    const [selectedModel, setSelectedModel] = useState<string>("mixtral-remote");
    const [isInitializing, setIsInitializing] = useState(true);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const { isOpen: isSidebarOpen, onToggle: toggleSidebar } = useDisclosure({ defaultIsOpen: true });

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
                setAvailableModels(models);
                setSessions(sessions);
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

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const currentInput = input;
        setInput('');
        setLoading(true);
        setError(null);

        try {
            const userMessage: ChatMessage = {
                role: 'user',
                content: currentInput,
                timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, userMessage]);

            const response = await submitPrompt(currentInput, selectedModel, activeSessionId || undefined);
            
            const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: response.response,
                timestamp: new Date().toISOString(),
                ipfsHash: response.ipfs_cid,
                transactionHash: response.transaction_hash,
                metadata: {
                    model: response.model_name,
                    model_id: response.model_id,
                    temperature: response.metadata.temperature,
                    max_tokens: response.metadata.max_tokens
                }
            };
            setMessages(prev => [...prev, assistantMessage]);

            if (!activeSessionId) {
                setActiveSessionId(response.session_id);
                const updatedSessions = await getSessions();
                setSessions(updatedSessions);
            }
        } catch (err) {
            console.error('Error submitting prompt:', err);
            setError(err instanceof Error ? err.message : 'Failed to get response');
        } finally {
            setLoading(false);
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setActiveSessionId(null);
    };

    const handleSelectSession = async (sessionId: string) => {
        try {
            const session = await getSession(sessionId);
            setMessages(session.messages);
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
                            {isLoading && (
                                <Box p={4} borderRadius="lg" bg={inputBgColor} maxW="80%" alignSelf="flex-start">
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
                                    isLoading={isLoading}
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