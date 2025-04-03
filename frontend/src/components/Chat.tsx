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
} from '@chakra-ui/react';
import { FiSend, FiRefreshCw, FiHash, FiLink } from 'react-icons/fi';
import { ChatMessage } from '../types/chat';
import { submitPrompt } from '../services/api';

export const Chat: React.FC = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
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

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: ChatMessage = {
            role: 'user',
            content: input.trim(),
            timestamp: new Date().toISOString(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        setError(null);

        try {
            const response = await submitPrompt(input.trim());
            const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: response.response,
                timestamp: new Date().toISOString(),
                ipfsHash: response.ipfs_cid,
                transactionHash: response.signature,
            };
            setMessages(prev => [...prev, assistantMessage]);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to get response');
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

    const handleRefresh = () => {
        setMessages([]);
        setError(null);
    };

    const formatHash = (hash: string) => {
        return `${hash.slice(0, 6)}...${hash.slice(-4)}`;
    };

    return (
        <Flex h="100vh" direction="column" bg={bgColor}>
            {/* Header */}
            <Box p={4} borderBottom="1px" borderColor={borderColor}>
                <Container maxW="3xl">
                    <HStack justify="space-between">
                        <Text fontSize="xl" fontWeight="bold" color={textColor}>
                            NeuroChain Chat
                        </Text>
                        <IconButton
                            aria-label="Refresh chat"
                            icon={<FiRefreshCw />}
                            onClick={handleRefresh}
                            variant="ghost"
                            size="sm"
                            isDisabled={isLoading}
                            color={textColor}
                        />
                    </HStack>
                </Container>
            </Box>

            {/* Main Chat Area */}
            <Flex flex={1} overflow="hidden">
                {/* Messages Container */}
                <Box flex={1} overflowY="auto" p={4}>
                    <Container maxW="3xl" h="100%">
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
                                    <Text color={textColor}>{message.content}</Text>
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
                                                    href={`https://basescan.org/tx/${message.transactionHash}`}
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
                                </Box>
                            ))}
                            {isLoading && (
                                <Box p={4} borderRadius="lg" bg={messageBgColor} maxW="80%">
                                    <Text color={textColor}>Thinking...</Text>
                                </Box>
                            )}
                            {error && (
                                <Box p={4} borderRadius="lg" bg="red.50" maxW="80%">
                                    <Text color="red.500">{error}</Text>
                                </Box>
                            )}
                            <div ref={messagesEndRef} />
                        </VStack>
                    </Container>
                </Box>
            </Flex>

            {/* Input Area */}
            <Box p={4} borderTop="1px" borderColor={borderColor}>
                <Container maxW="3xl">
                    <form onSubmit={handleSubmit}>
                        <HStack spacing={4}>
                            <Input
                                ref={inputRef}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="Type your message..."
                                size="lg"
                                borderRadius="full"
                                bg={inputBgColor}
                                borderColor={inputBorderColor}
                                color={inputTextColor}
                                _placeholder={{ color: placeholderColor }}
                                _focus={{
                                    borderColor: 'blue.500',
                                    boxShadow: '0 0 0 1px var(--chakra-colors-blue-500)',
                                }}
                            />
                            <Button
                                type="submit"
                                colorScheme="blue"
                                size="lg"
                                borderRadius="full"
                                isLoading={isLoading}
                                leftIcon={<FiSend />}
                            >
                                Send
                            </Button>
                        </HStack>
                    </form>
                </Container>
            </Box>
        </Flex>
    );
}; 