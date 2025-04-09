import { Box, Text, HStack, Link, Tooltip, useColorModeValue } from '@chakra-ui/react';
import { FiHash, FiLink } from 'react-icons/fi';
import { ChatMessage } from '../types/chat';
import React from 'react';
import VerificationBadge from './VerificationBadge';

interface ChatMessageProps {
    message: ChatMessage;
}

const formatHash = (hash: string) => {
    return `${hash.slice(0, 6)}...${hash.slice(-4)}`;
};

export default function ChatMessageComponent({ message }: ChatMessageProps) {
    const textColor = useColorModeValue('gray.800', 'gray.200');
    const messageBgColor = useColorModeValue('gray.50', 'gray.700');
    const userMessageBgColor = useColorModeValue('blue.50', 'blue.900');
    const timestampColor = useColorModeValue('gray.500', 'gray.400');
    const linkColor = useColorModeValue('blue.500', 'blue.300');

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
    const verificationHash = message.metadata?.verification_hash;
    const signature = message.metadata?.signature;

    return (
        <Box
            p={4}
            borderRadius="lg"
            bg={message.role === 'user' ? userMessageBgColor : messageBgColor}
            maxW="80%"
            alignSelf={message.role === 'user' ? 'flex-end' : 'flex-start'}
            mb={4}
        >
            <Text 
                color={textColor}
                whiteSpace="pre-line"
            >
                {message.content}
            </Text>
            
            {message.role === 'assistant' && verificationHash && signature && (
                <VerificationBadge
                    verification_hash={verificationHash}
                    signature={signature}
                    ipfs_cid={ipfsHash || ''}
                    transaction_hash={transactionHash || ''}
                />
            )}
            
            <HStack spacing={4} mt={2} fontSize="xs" color={timestampColor}>
                <Text>{new Date(message.timestamp).toLocaleTimeString()}</Text>
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