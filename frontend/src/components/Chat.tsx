import React, { useState, useRef, useEffect } from 'react';
import {
    Box,
    VStack,
    HStack,
    Button,
    Text,
    IconButton,
    useColorModeValue,
    Flex,
    Container,
    Select,
    FormControl,
    useDisclosure,
    Collapse,
    Textarea,
    useBreakpointValue,
    Spinner,
    Alert,
    AlertIcon,
    AlertTitle,
    AlertDescription,
    useToast,
    useColorMode
} from '@chakra-ui/react';
import { ChevronLeftIcon, ChevronRightIcon } from '@chakra-ui/icons';
import { ChatMessage } from '../types/chat';
import { submitPrompt, getSession } from '../services/api';
import Sidebar from './Sidebar';
import ChatMessageComponent from './ChatMessage';
import { useApp } from '../context/AppContext';
import { payForMessage } from '../services/blockchain';
import { FiMoon, FiSun } from 'react-icons/fi';

export default function Chat() {
    const {
        models: availableModels,
        sessions: availableSessions,
        userAddress,
        connectWallet,
        error,
        refreshSessions
    } = useApp();
    const { colorMode, toggleColorMode } = useColorMode();
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
    const { isOpen: isSidebarOpen, onToggle: toggleSidebar } = useDisclosure({ 
        defaultIsOpen: window.innerWidth >= 768 // Only open by default on desktop
    });
    const toast = useToast();

    const bgColor = useColorModeValue('gray.50', 'gray.900');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const messageBgColor = useColorModeValue('gray.50', 'gray.700');
    const textColor = useColorModeValue('gray.800', 'gray.200');
    const inputBgColor = useColorModeValue('white', 'gray.800');
    const inputBorderColor = useColorModeValue('gray.200', 'gray.600');
    const inputTextColor = useColorModeValue('gray.800', 'gray.200');
    const buttonBgColor = useColorModeValue('blue.500', 'blue.400');
    const buttonHoverBgColor = useColorModeValue('blue.600', 'blue.500');
    const iconColor = useColorModeValue('gray.800', 'gray.200');

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
                setMessages(session.messages);
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

    // Add a resize listener to handle sidebar state on window resize
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth >= 768 && !isSidebarOpen) {
                toggleSidebar();
            } else if (window.innerWidth < 768 && isSidebarOpen) {
                toggleSidebar();
            }
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [isSidebarOpen, toggleSidebar]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isThinking) return;

        if (!userAddress) {
            toast({
                title: 'Error',
                description: 'Please connect your wallet first',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
            return;
        }

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

        console.log("🔍 activeSessionId before payForMessage:", activeSessionId);
        console.log("🧵 Length of sessionId:", activeSessionId?.length);

        try {
            // Make payment first
            const safeSessionId = (activeSessionId && activeSessionId.length < 100) ? activeSessionId : 'new';
            await payForMessage(safeSessionId);
            
            const response = await submitPrompt(
                input,
                selectedModel,
                userAddress,
                activeSessionId || undefined
            );
            console.log('Prompt response:', response);
            console.log("🧪 Backend response.session_id:", response.session_id);


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

            // Update messages and turn off loading state in a single batch
            setMessages(prev => [...prev, assistantMessage]);
            setIsThinking(false);
            
            // Always refresh sessions after a successful response
            await refreshSessions();
            
            // Update active session if needed
            if (!activeSessionId && response.session_id) {
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

    const groupedModels = Object.entries(availableModels).reduce((acc, [name, id]) => {
        const provider = name.includes('local') ? 'Local' : 'Remote';
        if (!acc[provider]) {
            acc[provider] = [];
        }
        acc[provider].push({ name, id });
        return acc;
    }, {} as { [key: string]: { name: string; id: string }[] });


    return (
        <Flex h="100vh" bg={bgColor} position="relative">
            <IconButton
                aria-label="Toggle sidebar"
                icon={isSidebarOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
                onClick={toggleSidebar}
                position="absolute"
                left={isSidebarOpen ? { base: "calc(100% - 40px)", md: "300px" } : "0"}
                top="50%"
                transform="translateY(-50%)"
                zIndex={2}
                bg={inputBgColor}
                _hover={{ bg: buttonHoverBgColor }}
                transition="all 0.2s"
                size={{ base: 'sm', md: 'md' }}
                display={{ base: 'none', md: 'flex' }}
            />

            <IconButton
                aria-label="Open sidebar"
                icon={<ChevronRightIcon />}
                onClick={toggleSidebar}
                position="fixed"
                left={2}
                top={4}
                zIndex={2}
                bg={inputBgColor}
                _hover={{ bg: buttonHoverBgColor }}
                size="sm"
                display={{ base: 'flex', md: 'none' }}
            />

            <Collapse in={isSidebarOpen} animateOpacity>
                <Box
                    w={{ base: '100%', md: '300px' }}
                    h="100%"
                    borderRight="1px"
                    borderColor={borderColor}
                    bg={inputBgColor}
                    position={{ base: 'fixed', md: 'relative' }}
                    left={{ base: 0, md: 'auto' }}
                    zIndex={1}
                >
                    <Box position="relative" h="100%">
                        <IconButton
                            aria-label="Close sidebar"
                            icon={<ChevronLeftIcon />}
                            onClick={toggleSidebar}
                            position="absolute"
                            right={2}
                            top={2}
                            size="sm"
                            display={{ base: 'flex', md: 'none' }}
                        />
                        <Sidebar
                            sessions={availableSessions}
                            activeSessionId={activeSessionId}
                            onNewChat={handleNewChat}
                            onSelectSession={handleSelectSession}
                        />
                    </Box>
                </Box>
            </Collapse>

            <Flex 
                direction="column" 
                flex="1" 
                w="100%" 
                transition="all 0.2s"
                position="relative"
                overflow="hidden"
            >
                <Box p={{ base: 2, md: 4 }} borderBottom="1px" borderColor={borderColor} bg={inputBgColor}>
                    <Container maxW={maxMessageWidth}>
                        <Flex
                            direction={{ base: 'column', sm: 'row' }}
                            justify="space-between"
                            align={{ base: 'stretch', sm: 'center' }}
                            gap={{ base: 2, sm: 4 }}
                        >
                            <Text fontSize={{ base: 'xl', md: '2xl' }} fontWeight="bold" color={textColor}>
                                NeuroSpace Chat
                            </Text>
                            <HStack spacing={4} justify={{ base: 'space-between', sm: 'flex-end' }} w={{ base: '100%', sm: 'auto' }}>
                                <FormControl width={{ base: '100%', sm: '200px' }}>
                                    <Select
                                        value={selectedModel}
                                        onChange={(e) => setSelectedModel(e.target.value)}
                                        size={{ base: 'sm', md: 'md' }}
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
                                <IconButton
                                    aria-label="Toggle color mode"
                                    icon={colorMode === 'light' ? <FiMoon /> : <FiSun />}
                                    onClick={toggleColorMode}
                                    size={{ base: 'sm', md: 'md' }}
                                    colorScheme="blue"
                                    variant="ghost"
                                    color={iconColor}
                                />
                            </HStack>
                        </Flex>
                    </Container>
                </Box>

                {error && (
                    <Alert status="error" mb={4}>
                        <AlertIcon />
                        <AlertTitle>Error:</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                <Flex 
                    direction="column" 
                    flex="1" 
                    overflowY="auto" 
                    p={{ base: 2, md: 4 }}
                    position="relative"
                >
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

                <Box 
                    p={{ base: 2, md: 4 }} 
                    borderTop="1px" 
                    borderColor={borderColor} 
                    bg={inputBgColor}
                >
                    <Container maxW={maxMessageWidth}>
                        {!userAddress ? (
                            <Button 
                                onClick={connectWallet} 
                                colorScheme="blue"
                                size={{ base: 'sm', md: 'md' }}
                                w="100%"
                            >
                                Connect Wallet
                            </Button>
                        ) : (
                            <form onSubmit={handleSubmit}>
                                <HStack spacing={2}>
                                    <FormControl>
                                        <Textarea
                                            ref={inputRef}
                                            value={input}
                                            onChange={(e) => setInput(e.target.value)}
                                            placeholder="Type your message..."
                                            size={{ base: 'sm', md: 'md' }}
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
                                        px={{ base: 4, md: 6 }}
                                        size={{ base: 'sm', md: 'md' }}
                                    >
                                        Send (0.00001 ETH)
                                    </Button>
                                </HStack>
                            </form>
                        )}
                    </Container>
                </Box>
            </Flex>
        </Flex>
    );
} 