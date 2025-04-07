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
} from '@chakra-ui/react';
import { FiSend, FiRefreshCw, FiHash, FiLink } from 'react-icons/fi';
import { ChatMessage, ChatSession } from '../types/chat';
import { submitPrompt, getAvailableModels, Model, getSessions, getSession, API_BASE_URL } from '../services/api';
import { Sidebar } from './Sidebar';

export const Chat: React.FC = () => {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [availableModels, setAvailableModels] = useState<Model[]>([]);
    const [selectedModel, setSelectedModel] = useState<string>('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const messageBgColor = useColorModeValue('gray.50', 'gray.700');
    const userMessageBgColor = useColorModeValue('blue.50', 'blue.900');
    const textColor = useColorModeValue('gray.800', 'white');
    const linkColor = useColorModeValue('blue.500', 'blue.300');
    const inputBgColor = useColorModeValue('white', 'gray.700');
    const inputBorderColor = useColorModeValue('gray.200', 'gray.600');
    const inputTextColor = useColorModeValue('gray.800', 'white');
    const placeholderColor = useColorModeValue('gray.500', 'gray.400');
    const timestampColor = useColorModeValue('gray.500', 'gray.400');

    // Load available models and sessions on component mount
    useEffect(() => {
        const loadInitialData = async () => {
            try {
                const [models, sessions] = await Promise.all([
                    getAvailableModels(),
                    getSessions()
                ]);
                setAvailableModels(models);
                if (models.length > 0) {
                    setSelectedModel(models[0].name);
                }
                setSessions(sessions);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load data');
            }
        };
        
        loadInitialData();
    }, []);

    // Load session messages when active session changes
    useEffect(() => {
        const loadSessionMessages = async () => {
            if (activeSessionId) {
                try {
                    const session = await getSession(activeSessionId);
                    setMessages(session.messages);
                } catch (err) {
                    setError(err instanceof Error ? err.message : 'Failed to load session');
                }
            } else {
                setMessages([]);
            }
        };
        
        loadSessionMessages();
    }, [activeSessionId]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        // Create and show user message immediately
        const userMessage: ChatMessage = {
            role: 'user',
            content: input.trim(),
            timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, userMessage]);

        setInput('');
        setIsLoading(true);
        setError(null);

        try {
            let response;
            
            try {
                // Try with axios first
                response = await submitPrompt(
                    input.trim(),
                    selectedModel,
                    activeSessionId || undefined
                );
                console.log('Backend response:', response);
            } catch (axiosError) {
                console.error('Axios request failed, trying with fetch:', axiosError);
                
                // Fallback to fetch if axios fails
                const fetchResponse = await fetch(`${API_BASE_URL}/prompt`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-User-Address': '0x1234567890123456789012345678901234567890'
                    },
                    body: JSON.stringify({
                        prompt: input.trim(),
                        model_name: selectedModel,
                        session_id: activeSessionId || undefined
                    })
                });
                
                if (!fetchResponse.ok) {
                    throw new Error(`Fetch failed with status: ${fetchResponse.status}`);
                }
                
                response = await fetchResponse.json();
                console.log('Backend response (fetch):', response);
            }

            // Create assistant message with all metadata
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
            console.log('Created assistant message:', assistantMessage);

            // Add assistant message to the UI
            setMessages(prev => [...prev, assistantMessage]);
            
            // If this was a new chat, update the active session and load the session
            if (!activeSessionId) {
                setActiveSessionId(response.session_id);
                // Load the session to get all messages with metadata
                const session = await getSession(response.session_id);
                setMessages(session.messages);
                // Refresh sessions to include the new one
                const updatedSessions = await getSessions();
                setSessions(updatedSessions);
            }
        } catch (err) {
            console.error('Chat component error:', err);
            
            // Display a more user-friendly error message
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError('An unknown error occurred while processing your request');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const handleNewChat = () => {
        setActiveSessionId(null);
        setMessages([]);
        setError(null);
    };

    const handleSelectSession = (sessionId: string) => {
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

    return (
        <Flex h="100vh" bg={bgColor}>
            <Sidebar
                sessions={sessions}
                activeSessionId={activeSessionId}
                onNewChat={handleNewChat}
                onSelectSession={handleSelectSession}
            />

            <Flex direction="column" flex="1">
                {/* Header with title and model selection */}
                <Box p={4} borderBottom="1px" borderColor={borderColor}>
                    <Container maxW="container.md">
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
                                    {availableModels.map((model) => (
                                        <option key={model.name} value={model.name}>
                                            {model.name}
                                        </option>
                                    ))}
                                </Select>
                            </FormControl>
                        </HStack>
                    </Container>
                </Box>

                <Box flex="1" overflowY="auto" p={4}>
                    <Container maxW="container.md">
                        <VStack spacing={4} align="stretch">
                            {messages.map((message, index) => (
                                <Box
                                    key={index}
                                    p={4}
                                    borderRadius="lg"
                                    bg={message.role === 'user' ? userMessageBgColor : messageBgColor}
                                    maxW="80%"
                                    alignSelf={message.role === 'user' ? 'flex-end' : 'flex-start'}
                                >
                                    <Text 
                                        color={textColor}
                                        whiteSpace="pre-line"
                                    >
                                        {message.content}
                                    </Text>
                                    
                                    <HStack spacing={4} mt={2} fontSize="xs" color={timestampColor}>
                                        <Text>{new Date(message.timestamp).toLocaleTimeString()}</Text>
                                        {message.ipfsHash && (
                                            <Tooltip label="View on IPFS">
                                                <Link
                                                    href={`https://ipfs.io/ipfs/${message.ipfsHash}`}
                                                    isExternal
                                                    color={linkColor}
                                                    display="flex"
                                                    alignItems="center"
                                                    gap={1}
                                                >
                                                    <FiHash />
                                                    {formatHash(message.ipfsHash)}
                                                </Link>
                                            </Tooltip>
                                        )}
                                        {message.transactionHash && (
                                            <Tooltip label="View on BaseScan">
                                                <Link
                                                    href={`https://sepolia.basescan.org/tx/${message.transactionHash}`}
                                                    isExternal
                                                    color={linkColor}
                                                    display="flex"
                                                    alignItems="center"
                                                    gap={1}
                                                >
                                                    <FiLink />
                                                    {formatHash(message.transactionHash)}
                                                </Link>
                                            </Tooltip>
                                        )}
                                    </HStack>
                                    {message.role === 'assistant' && renderMetadata(message)}
                                </Box>
                            ))}
                            {isLoading && (
                                <Box p={4} borderRadius="lg" bg={messageBgColor} maxW="80%">
                                    <Text color={textColor}>Thinking...</Text>
                                </Box>
                            )}
                            {error && (
                                <Box p={4} borderRadius="lg" bg="red.100" maxW="100%">
                                    <Text fontWeight="bold" color="red.600">Error:</Text>
                                    <Text color="red.600">{error}</Text>
                                    <Box mt={2}>
                                        <Text fontSize="sm" color="red.600">
                                            Troubleshooting tips:
                                        </Text>
                                        <UnorderedList fontSize="sm" color="red.600" pl={4}>
                                            <ListItem>Check that the API server is running at {API_BASE_URL}</ListItem>
                                            <ListItem>Ensure your prompt doesn't contain any inappropriate content</ListItem>
                                            <ListItem>Try selecting a different model</ListItem>
                                            <ListItem>Check the browser console for detailed error information</ListItem>
                                        </UnorderedList>
                                    </Box>
                                </Box>
                            )}
                            <div ref={messagesEndRef} />
                        </VStack>
                    </Container>
                </Box>

                <Box p={4} borderTop="1px" borderColor={borderColor}>
                    <Container maxW="container.md">
                        <form onSubmit={handleSubmit}>
                            <VStack spacing={4}>
                                <HStack w="100%">
                                    <Input
                                        ref={inputRef}
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        onKeyPress={handleKeyPress}
                                        placeholder="Type your message..."
                                        size="lg"
                                        bg={inputBgColor}
                                        borderColor={inputBorderColor}
                                        color={inputTextColor}
                                        _placeholder={{ color: placeholderColor }}
                                    />
                                    <IconButton
                                        aria-label="Send message"
                                        icon={<FiSend />}
                                        type="submit"
                                        colorScheme="blue"
                                        size="lg"
                                        isLoading={isLoading}
                                    />
                                </HStack>
                                
                                {error && (
                                    <Button 
                                        onClick={async () => {
                                            try {
                                                const response = await fetch(`${API_BASE_URL}/health`);
                                                const data = await response.json();
                                                alert(`API Health Check: ${JSON.stringify(data, null, 2)}`);
                                            } catch (err) {
                                                alert(`Failed to connect to API: ${err}`);
                                            }
                                        }}
                                        size="sm"
                                        colorScheme="red"
                                    >
                                        Test API Connection
                                    </Button>
                                )}
                            </VStack>
                        </form>
                    </Container>
                </Box>
            </Flex>
        </Flex>
    );
}; 