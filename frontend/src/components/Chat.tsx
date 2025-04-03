import React, { useState, useRef, useEffect } from 'react';
import {
    Box,
    VStack,
    HStack,
    Input,
    Button,
    Text,
    Container,
    Flex,
    IconButton,
    Spinner,
} from '@chakra-ui/react';
import { FiSend, FiRefreshCw } from 'react-icons/fi';
import { Message } from '../types/chat';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const Chat: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            content: input.trim(),
            role: 'user',
            timestamp: new Date().toISOString(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        setError(null);

        try {
            console.log('Sending request with headers:', {
                'Content-Type': 'application/json',
                'X-User-Address': '0x1234567890123456789012345678901234567890'
            });
            
            const response = await axios.post(`${API_URL}/prompts`, {
                prompt: input.trim(),
                timestamp: new Date().toISOString(),
            }, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-Address': '0x1234567890123456789012345678901234567890',
                },
                withCredentials: false,
            });

            console.log('Response received:', response.data);
            
            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                content: response.data.response,
                role: 'assistant',
                timestamp: new Date().toISOString(),
                ipfsHash: response.data.ipfs_cid,
                transactionHash: response.data.signature,
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            if (axios.isAxiosError(error)) {
                console.error('Axios error:', {
                    status: error.response?.status,
                    data: error.response?.data,
                    headers: error.response?.headers,
                });
            } else {
                console.error('Error:', error);
            }
            setError('Failed to send message. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const clearChat = () => {
        setMessages([]);
        setError(null);
    };

    return (
        <Container maxW="container.md" h="100vh" py={4}>
            <VStack h="full" gap={4}>
                <Flex w="full" justify="space-between" align="center">
                    <Text fontSize="2xl" fontWeight="bold">NeuroChain Chat</Text>
                    <Button
                        aria-label="Clear chat"
                        onClick={clearChat}
                        variant="ghost"
                    >
                        <FiRefreshCw style={{ marginRight: '8px' }} />
                        Clear
                    </Button>
                </Flex>

                {error && (
                    <Box w="full" p={4} bg="red.50" color="red.700" borderRadius="md">
                        {error}
                    </Box>
                )}

                <Box
                    flex={1}
                    w="full"
                    overflowY="auto"
                    bg="white"
                    borderRadius="lg"
                    p={4}
                    boxShadow="sm"
                    css={{
                        '&::-webkit-scrollbar': {
                            width: '4px',
                        },
                        '&::-webkit-scrollbar-track': {
                            width: '6px',
                            background: '#f1f1f1',
                        },
                        '&::-webkit-scrollbar-thumb': {
                            background: '#888',
                            borderRadius: '24px',
                        },
                    }}
                >
                    {messages.map((message) => (
                        <Box
                            key={message.id}
                            mb={4}
                            bg={message.role === 'user' ? 'blue.50' : 'white'}
                            p={4}
                            borderRadius="lg"
                            boxShadow="sm"
                        >
                            <Text fontWeight="bold" mb={2}>
                                {message.role === 'user' ? 'You' : 'Assistant'}
                            </Text>
                            <Text whiteSpace="pre-wrap">{message.content}</Text>
                            {message.ipfsHash && (
                                <Box mt={2} fontSize="sm" color="gray.500">
                                    <Text>IPFS Hash: {message.ipfsHash}</Text>
                                    <Text>Transaction Hash: {message.transactionHash}</Text>
                                </Box>
                            )}
                        </Box>
                    ))}
                    {isLoading && (
                        <Flex justify="center" align="center" py={4}>
                            <Spinner />
                        </Flex>
                    )}
                    <div ref={messagesEndRef} />
                </Box>

                <form onSubmit={handleSubmit} style={{ width: '100%' }}>
                    <HStack>
                        <Input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type your message..."
                            size="lg"
                            disabled={isLoading}
                        />
                        <Button
                            type="submit"
                            colorScheme="blue"
                            size="lg"
                            isLoading={isLoading}
                            disabled={!input.trim() || isLoading}
                        >
                            <FiSend />
                        </Button>
                    </HStack>
                </form>
            </VStack>
        </Container>
    );
}; 