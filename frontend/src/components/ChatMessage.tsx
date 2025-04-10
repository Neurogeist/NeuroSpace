import React from 'react';
import {
    Box,
    VStack,
    HStack,
    Text,
    useColorModeValue,
    Link,
    Tooltip,
    Code,
    UnorderedList,
    ListItem,
    OrderedList,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    Image,
    Divider
} from '@chakra-ui/react';
import ReactMarkdown from 'react-markdown';
import { Components } from 'react-markdown';
import { ChatMessage as ChatMessageType } from '../types/chat';
import VerificationBadge from './VerificationBadge';

interface ChatMessageProps {
    message: ChatMessageType;
}

const components: Components = {
    p: ({ children }) => <Text mb={2}>{children}</Text>,
    h1: ({ children }) => <Text as="h1" fontSize="2xl" fontWeight="bold" mb={4}>{children}</Text>,
    h2: ({ children }) => <Text as="h2" fontSize="xl" fontWeight="bold" mb={3}>{children}</Text>,
    h3: ({ children }) => <Text as="h3" fontSize="lg" fontWeight="bold" mb={2}>{children}</Text>,
    ul: ({ children }) => <UnorderedList mb={2}>{children}</UnorderedList>,
    ol: ({ children }) => <OrderedList mb={2}>{children}</OrderedList>,
    li: ({ children }) => <ListItem>{children}</ListItem>,
    code: ({ children }) => <Code p={2} borderRadius="md">{children}</Code>,
    pre: ({ children }) => <Box as="pre" p={4} borderRadius="md" bg="gray.100" overflowX="auto">{children}</Box>,
    table: ({ children }) => <Table variant="simple" mb={4}>{children}</Table>,
    thead: ({ children }) => <Thead>{children}</Thead>,
    tbody: ({ children }) => <Tbody>{children}</Tbody>,
    tr: ({ children }) => <Tr>{children}</Tr>,
    th: ({ children }) => <Th>{children}</Th>,
    td: ({ children }) => <Td>{children}</Td>,
    a: ({ href, children }) => (
        <Link href={href} color="blue.500" isExternal>
            {children}
        </Link>
    ),
    img: ({ src, alt }) => (
        <Image src={src} alt={alt} maxW="100%" borderRadius="md" />
    ),
    hr: () => <Divider my={4} />,
    blockquote: ({ children }) => (
        <Box
            as="blockquote"
            pl={4}
            borderLeft="4px"
            borderColor="gray.200"
            fontStyle="italic"
            mb={4}
        >
            {children}
        </Box>
    ),
};

export default function ChatMessage({ message }: ChatMessageProps) {
    const bgColor = useColorModeValue(
        message.role === 'user' ? 'blue.50' : 'gray.50',
        message.role === 'user' ? 'blue.900' : 'gray.700'
    );
    const textColor = useColorModeValue('gray.800', 'gray.200');
    const borderColor = useColorModeValue('gray.200', 'gray.600');
    const timestampColor = useColorModeValue('gray.500', 'gray.400');

    const verificationHash = message.metadata?.verification_hash || message.verification_hash;
    const signature = message.metadata?.signature || message.signature;
    const ipfsCid = message.metadata?.ipfs_cid || message.ipfsHash;
    const transactionHash = message.metadata?.transaction_hash || message.transactionHash;

    return (
        <Box
            p={4}
            borderRadius="lg"
            bg={bgColor}
            maxW="80%"
            alignSelf={message.role === 'user' ? 'flex-end' : 'flex-start'}
            border="1px"
            borderColor={borderColor}
        >
            <VStack align="stretch" spacing={2}>
                <HStack justify="space-between">
                    <Text fontWeight="bold" color={textColor}>
                        {message.role === 'user' ? 'You' : 'Assistant'}
                    </Text>
                    <Text fontSize="xs" color={timestampColor}>
                        {new Date(message.timestamp).toLocaleString()}
                    </Text>
                </HStack>

                {message.role === 'assistant' ? (
                    <>
                        <ReactMarkdown components={components}>
                            {message.content}
                        </ReactMarkdown>
                        {verificationHash && signature && (
                            <Box mt={2}>
                                <VerificationBadge
                                    verification_hash={verificationHash}
                                    signature={signature}
                                    ipfs_cid={ipfsCid}
                                    transaction_hash={transactionHash}
                                />
                            </Box>
                        )}
                    </>
                ) : (
                    <Text color={textColor}>{message.content}</Text>
                )}
            </VStack>
        </Box>
    );
} 