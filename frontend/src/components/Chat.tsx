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
import { submitPrompt, getSession, createSession } from '../services/api';
import Sidebar from './Sidebar';
import ChatMessageComponent from './ChatMessage';
import { useApp } from '../context/AppContext';
import { payForMessage } from '../services/blockchain';
import { FiMoon, FiSun, FiHome } from 'react-icons/fi';
import { Link as RouterLink } from 'react-router-dom';

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
        const savedSessionId = localStorage.getItem('activeSessionId');
        return savedSessionId || null;
    });
    const [selectedModel, setSelectedModel] = useState<string>(() => {
        const savedModel = localStorage.getItem('selectedModel');
        return savedModel || 'mixtral-8x7b-instruct';
    });
    const [thinkingStatus, setThinkingStatus] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const { isOpen: isSidebarOpen, onToggle: toggleSidebar } = useDisclosure({ 
        defaultIsOpen: window.innerWidth >= 768
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
        if (availableSessions.length > 0 && !activeSessionId) {
            setActiveSessionId(availableSessions[0].session_id);
        }
    }, [availableSessions]);

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
        if (!input.trim() || thinkingStatus) return;

        e.preventDefault();
        if (!userAddress) {
            toast({ title: "Connect wallet", status: "error" });
            return;
        }

        setThinkingStatus("Processing Payment...");

        const userMessage: ChatMessage = { content: input, role: "user", timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMessage]);
        setInput('');

        let sessionId = activeSessionId;
        let createdNewSession = false;

        try {
            if (!sessionId) {
                const sessionResponse = await createSession(userAddress);
                sessionId = sessionResponse.session_id;
                createdNewSession = true;
                console.log("🆕 Created new session:", sessionId);
            }

            const tx = await payForMessage(sessionId);
            console.log("💵 Payment transaction hash:", tx.hash);

            await tx.wait();
            console.log("✅ Payment confirmed on chain");

            setThinkingStatus("Thinking...");

            await submitPrompt(
                input,
                selectedModel,
                userAddress,
                sessionId,
                tx.hash
            );
    
            await refreshSessions();
            const session = await getSession(sessionId);
            setMessages(session.messages);
    
            if (createdNewSession) {
                setActiveSessionId(sessionId);
                localStorage.setItem('activeSessionId', sessionId);
            }
    
        } catch (err) {
            const error = err as any;
            console.error('Error during prompt submission:', error);
        
            let errorMessage = "An unexpected error occurred.";
            if (error?.code === "ACTION_REJECTED") {
                errorMessage = "Payment cancelled.";
            } else if (error instanceof Error) {
                errorMessage = error.message;
            }
        
            toast({
                title: "Submission Error",
                description: errorMessage,
                status: "error",
            });
        
            if (error?.code === "ACTION_REJECTED") {
                setMessages(prev => prev.slice(0, -1));
            }
        } finally {
            setThinkingStatus(null);
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

    const formatModelName = (name: string) => {
        if (window.innerWidth < 768) {
            return name.length > 20 ? `${name.slice(0, 17)}...` : name;
        }
        return name;
    };

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
                top={2}
                zIndex={2}
                bg={inputBgColor}
                _hover={{ bg: buttonHoverBgColor }}
                size="sm"
                display={{ base: 'flex', md: 'none' }}
            />

            <IconButton
                as={RouterLink}
                to="/"
                aria-label="Go to home"
                icon={<FiHome />}
                position="fixed"
                right={2}
                top={2}
                zIndex={2}
                bg={inputBgColor}
                _hover={{ bg: buttonHoverBgColor }}
                size="sm"
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
                            position="relative"
                            pl={{ base: 10, md: 0 }}
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
                                                        {formatModelName(name)}
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
                        <AlertTitle fontSize={{ base: 'sm', md: 'md' }}>Error:</AlertTitle>
                        <AlertDescription fontSize={{ base: 'sm', md: 'md' }}>{error}</AlertDescription>
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
                                <ChatMessageComponent 
                                    key={index} 
                                    message={message} 
                                    isSidebarOpen={isSidebarOpen}
                                />
                            ))}
                            
                            {thinkingStatus && (
                                <Box p={4} borderRadius="lg" bg={messageBgColor} maxW="80%" alignSelf="flex-start">
                                    <HStack>
                                        <Spinner size="sm" />
                                        <Text>{thinkingStatus}</Text>
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
                                        isLoading={!!thinkingStatus}
                                        isDisabled={!input.trim()}
                                        px={{ base: 4, md: 6 }}
                                        size={{ base: 'sm', md: 'md' }}
                                    >
                                        <Text display={{ base: 'none', sm: 'block' }}>Send (0.00001 ETH)</Text>
                                        <Text display={{ base: 'block', sm: 'none' }}>Send</Text>
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