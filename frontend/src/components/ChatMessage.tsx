import { Box, Text, HStack, Link, Tooltip, useColorModeValue, Code } from '@chakra-ui/react';
import { FiHash, FiLink } from 'react-icons/fi';
import { ChatMessage } from '../types/chat';
import React, { useState, useEffect } from 'react';
import { verifyMessage } from '../services/api';
import VerificationStatus from './VerificationStatus';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Components } from 'react-markdown';

interface ChatMessageProps {
    message: ChatMessage;
}

interface CodeProps {
    inline?: boolean;
    children: React.ReactNode;
}

const formatHash = (hash: string) => {
    return `${hash.slice(0, 6)}...${hash.slice(-4)}`;
};

const MarkdownComponents: Components = {
    p: ({ children }) => <Text mb={2}>{children}</Text>,
    em: ({ children }) => <Text as="em">{children}</Text>,
    strong: ({ children }) => <Text as="strong" fontWeight="bold">{children}</Text>,
    code: (props) => {
        const { inline, children } = props as { inline?: boolean; children: React.ReactNode };
        if (inline) {
            return <Code p={1} borderRadius="md">{children}</Code>;
        }
        return (
            <Box
                as="pre"
                p={3}
                bg={useColorModeValue('gray.100', 'gray.800')}
                borderRadius="md"
                overflowX="auto"
                whiteSpace="pre-wrap"
                fontSize="sm"
                fontFamily="mono"
                border="1px solid"
                borderColor={useColorModeValue('gray.200', 'gray.700')}
            >
                <Text color={useColorModeValue('gray.800', 'gray.100')}>{children}</Text>
            </Box>
        );
    },
    ul: ({ children }) => <Box as="ul" pl={4} mb={2}>{children}</Box>,
    ol: ({ children }) => <Box as="ol" pl={4} mb={2}>{children}</Box>,
    li: ({ children }) => <Box as="li" mb={1}>{children}</Box>,
    a: ({ href, children }) => (
        <Link href={href} color="blue.500" isExternal>
            {children}
        </Link>
    ),
};

export default function ChatMessageComponent({ message }: ChatMessageProps) {
    const [verificationResult, setVerificationResult] = useState<any>(null);
    const [isVerifying, setIsVerifying] = useState(false);
    const [verificationError, setVerificationError] = useState<string | null>(null);

    const textColor = useColorModeValue('gray.800', 'gray.200');
    const messageBgColor = useColorModeValue('gray.50', 'gray.700');
    const userMessageBgColor = useColorModeValue('blue.50', 'blue.900');
    const timestampColor = useColorModeValue('gray.500', 'gray.400');
    const linkColor = useColorModeValue('blue.500', 'blue.300');

    useEffect(() => {
        const verifySignature = async () => {
            if (
                message.role === 'assistant' && 
                message.metadata?.verification_hash && 
                message.metadata?.signature
            ) {
                // Check session storage first
                const storedResult = sessionStorage.getItem(`verification_${message.metadata.verification_hash}`);
                if (storedResult) {
                    setVerificationResult(JSON.parse(storedResult));
                    return;
                }

                try {
                    setIsVerifying(true);
                    setVerificationError(null);
                    console.log('Verifying message:', {
                        verification_hash: message.metadata.verification_hash,
                        signature: message.metadata.signature,
                        messageId: message.timestamp
                    });
                    
                    const result = await verifyMessage(
                        message.metadata.verification_hash,
                        message.metadata.signature
                    );
                    
                    console.log('Verification result:', result);
                    setVerificationResult(result);
                    // Store result in session storage
                    sessionStorage.setItem(`verification_${message.metadata.verification_hash}`, JSON.stringify(result));
                } catch (error) {
                    console.error('Error verifying message:', error);
                    setVerificationError('Failed to verify message');
                } finally {
                    setIsVerifying(false);
                }
            }
        };

        // Try verification immediately
        verifySignature();

        // If verification hasn't succeeded after 2 seconds, try again
        const timeoutId = setTimeout(() => {
            if (!verificationResult && !verificationError) {
                verifySignature();
            }
        }, 2000);

        return () => clearTimeout(timeoutId);
    }, [message]);

    const renderMetadata = (message: ChatMessage) => {
        if (!message.metadata) return null;
        
        return (
            <Box mt={2} fontSize="xs" color={timestampColor}>
                <HStack spacing={4}>
                    <Text fontWeight="bold">Model: {message.metadata.model}</Text>
                    <Text>Temperature: {message.metadata.temperature}</Text>
                    <Text>Max Tokens: {message.metadata.max_tokens}</Text>
                </HStack>
            </Box>
        );
    };

    // Get hash information from either root level or metadata
    const ipfsHash = message.ipfsHash || message.metadata?.ipfs_cid;
    const transactionHash = message.transactionHash || message.metadata?.transaction_hash;

    return (
        <Box
            p={4}
            borderRadius="lg"
            bg={message.role === 'user' ? userMessageBgColor : messageBgColor}
            maxW="80%"
            alignSelf={message.role === 'user' ? 'flex-end' : 'flex-start'}
            mb={4}
        >
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={MarkdownComponents}
            >
                {message.content}
            </ReactMarkdown>
            
            {message.role === 'assistant' && message.metadata?.verification_hash && (
                <VerificationStatus
                    verificationResult={verificationResult}
                    isLoading={isVerifying}
                    error={verificationError || undefined}
                />
            )}
            
            <HStack spacing={4} mt={2} fontSize="xs" color={timestampColor}>
                <Text>
                    {new Date(message.timestamp).toLocaleTimeString('en-US', {
                        hour: 'numeric',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: true
                    })}
                </Text>
                {ipfsHash && (
                    <Tooltip label="View on IPFS">
                        <Link
                            href={`https://ipfs.io/ipfs/${ipfsHash}`}
                            isExternal
                            color={linkColor}
                            display="flex"
                            alignItems="center"
                            gap={1}
                        >
                            <FiHash />
                            {formatHash(ipfsHash)}
                        </Link>
                    </Tooltip>
                )}
                {transactionHash && (
                    <Tooltip label="View on BaseScan">
                        <Link
                            href={`https://sepolia.basescan.org/tx/${transactionHash}`}
                            isExternal
                            color={linkColor}
                            display="flex"
                            alignItems="center"
                            gap={1}
                        >
                            <FiLink />
                            {formatHash(transactionHash)}
                        </Link>
                    </Tooltip>
                )}
            </HStack>
            {message.role === 'assistant' && renderMetadata(message)}
        </Box>
    );
} 