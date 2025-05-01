import { Box, Text, HStack, Link, Tooltip, useColorModeValue, Code, useBreakpointValue } from '@chakra-ui/react';
import { FiHash, FiLink } from 'react-icons/fi';
import { ChatMessage } from '../types/chat';
import React, { useState, useEffect } from 'react';
import { verifyMessage } from '../services/api';
import VerificationStatus from './VerificationStatus';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Components } from 'react-markdown';
import { verifyHash } from '../utils/verification';

const blockExplorerUrl =
  import.meta.env.VITE_ENVIRONMENT?.toLowerCase() === 'production'
    ? 'https://basescan.org'
    : 'https://sepolia.basescan.org';

interface ChatMessageProps {
    message: ChatMessage;
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
    ol: ({ children }) => (
        <Box as="ol" pl={4} mb={2} style={{ listStylePosition: 'inside' }}>
            {children}
        </Box>
    ),      
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
    const [hashMatch, setHashMatch] = useState<boolean | undefined>(undefined);

    const messageBgColor = useColorModeValue('gray.50', 'gray.700');
    const userMessageBgColor = useColorModeValue('blue.50', 'blue.900');
    const timestampColor = useColorModeValue('gray.500', 'gray.400');
    const linkColor = useColorModeValue('blue.500', 'blue.300');

    useEffect(() => {
        if (message.role !== 'assistant') return;
    
        const metadata = message.metadata;
        if (!metadata?.verification_hash || !metadata?.signature) return;
    
        const key = `verification_${metadata.verification_hash}`;
    
        const storedResult = sessionStorage.getItem(key);
        if (storedResult) {
            setVerificationResult(JSON.parse(storedResult));
            return;
        }
    
        let isMounted = true;
    
        const verifySignature = async () => {
            try {
                setIsVerifying(true);
                setVerificationError(null);
                setHashMatch(undefined);

                const verificationData = {
                    prompt: metadata.original_prompt || '',
                    response: message.content,
                    model_name: metadata.model || '',
                    model_id: metadata.model_id || '',
                    temperature: metadata.temperature || 0,
                    max_tokens: metadata.max_tokens || 0,
                    system_prompt: null,
                    timestamp: metadata.timestamp || '',
                    wallet_address: metadata.wallet_address || '', // pass this in metadata if not already
                    session_id: metadata.session_id || '',         // same here
                    rag_sources: [],
                    tool_calls: []
                };

                console.log('🔍 Verification Data:', {
                    verificationData,
                    metadata,
                    messageContent: message.content
                });

                if (!metadata.verification_hash) {
                    console.error('❌ No verification hash found');
                    setHashMatch(false);
                    return;
                }

                const hashIsValid = await verifyHash(verificationData, metadata.verification_hash);
                console.log('🔐 Hash match:', hashIsValid);
                setHashMatch(hashIsValid);

                if (!hashIsValid) {
                    console.error('❌ Hash verification failed');
                    return;
                }

                console.log('Verifying message:', {
                    verification_hash: metadata.verification_hash,
                    signature: metadata.signature,
                    messageId: message.timestamp
                });

                const result = await verifyMessage(
                    metadata.verification_hash!,
                    metadata.signature!,
                    undefined,
                    'ChatMessage'
                );                
    
                if (!isMounted) return;
    
                setVerificationResult(result);
                sessionStorage.setItem(key, JSON.stringify(result));
            } catch (error) {
                if (isMounted) {
                    console.error('Error verifying message:', error);
                    setVerificationError('Failed to verify message');
                }
            } finally {
                if (isMounted) setIsVerifying(false);
            }
        };
    
        verifySignature();
    
        return () => {
            isMounted = false;
        };
    }, [
        message.metadata?.verification_hash,
        message.metadata?.signature,
        message.role,
        message.timestamp,
        message.content
    ]);
    
    const renderMetadata = (message: ChatMessage) => {
        if (!message.metadata) return null;
        
        return (
            <Box mt={2} fontSize="xs" color={timestampColor}>
                <HStack spacing={4} wrap="wrap">
                    <Text fontWeight="bold">Model: {message.metadata.model}</Text>
                    <Text>Temperature: {message.metadata.temperature}</Text>
                    <Text>Max Tokens: {message.metadata.max_tokens}</Text>
                </HStack>
            </Box>
        );
    };

    const ipfsHash = message.metadata?.ipfs_cid;
    const transactionHash = message.metadata?.transaction_hash;

    const padding = useBreakpointValue({ base: 3, md: 4 });
    const spacing = useBreakpointValue({ base: 2, md: 4 });
    const maxWidth = useBreakpointValue({ base: '90%', md: '80%' });

    return (
        <Box
            p={padding}
            borderRadius="lg"
            bg={message.role === 'user' ? userMessageBgColor : messageBgColor}
            maxW={maxWidth}
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
                <Box mt={2}>
                    <VerificationStatus
                        verificationResult={verificationResult}
                        isLoading={isVerifying}
                        error={verificationError || undefined}
                        hashMatch={hashMatch}
                    />
                </Box>
            )}
        
            <HStack 
                spacing={spacing} 
                mt={2} 
                fontSize="xs" 
                color={timestampColor}
                flexWrap="wrap"
            >
                <Text>
                    {new Date(message.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: true
                    })}
                </Text>
                {message.role === 'assistant' && ipfsHash && (
                    <Tooltip label="View on IPFS">
                        <Link
                            href={`https://ipfs.io/ipfs/${ipfsHash}`}
                            isExternal
                            color={linkColor}
                            display="flex"
                            alignItems="center"
                            gap={1}
                            fontSize="xs"
                        >
                            <FiHash />
                            {formatHash(ipfsHash)}
                        </Link>
                    </Tooltip>
                )}
        
                {message.role === 'assistant' && transactionHash && (
                    <Tooltip label="View on BaseScan">
                        <Link
                            href={`${blockExplorerUrl}/tx/${transactionHash}`}
                            isExternal
                            color={linkColor}
                            display="flex"
                            alignItems="center"
                            gap={1}
                            fontSize="xs"
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