import React, { useState, useEffect } from 'react';
import {
    Box,
    VStack,
    HStack,
    Text,
    Button,
    useToast,
    useColorModeValue,
    Link,
    Tooltip,
    Textarea,
    Badge,
    Code,
    Accordion,
    AccordionItem,
    AccordionButton,
    AccordionPanel,
    AccordionIcon,
} from '@chakra-ui/react';
import { FiHash, FiLink } from 'react-icons/fi';
import { getAgents, queryAgent, Agent, AgentQueryResponse } from '../services/agents';
import { useWallet } from '../hooks/useWallet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Components } from 'react-markdown';

export default function AgentsPage() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
    const [query, setQuery] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [response, setResponse] = useState<AgentQueryResponse | null>(null);
    const toast = useToast();
    const { address, connect, isConnected, provider } = useWallet();

    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const linkColor = useColorModeValue('blue.500', 'blue.300');
    const textColor = useColorModeValue('gray.800', 'gray.100');
    const cardBgColor = useColorModeValue('white', 'gray.800');
    const headerBgColor = useColorModeValue('gray.50', 'gray.800');
    const codeBgColor = useColorModeValue('gray.100', 'gray.800');
    const codeBorderColor = useColorModeValue('gray.200', 'gray.700');
    const codeTextColor = useColorModeValue('gray.800', 'gray.100');
    const agentCardBgColor = useColorModeValue('gray.50', 'gray.700');
    const responseBgColor = useColorModeValue('gray.50', 'gray.700');

    const blockExplorerUrl = import.meta.env.VITE_ENVIRONMENT?.toLowerCase() === 'production'
        ? 'https://basescan.org'
        : 'https://sepolia.basescan.org';

    useEffect(() => {
        if (isConnected && address) {
            loadAgents();
        }
    }, [isConnected, address]);

    const loadAgents = async () => {
        if (!provider) {
            toast({
                title: 'Error',
                description: 'Wallet provider not available',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
            return;
        }

        try {
            const agentsList = await getAgents((address as string) || '', provider);
            setAgents(agentsList);
        } catch (error) {
            console.error('Error loading agents:', error);
            toast({
                title: 'Error',
                description: 'Failed to load agents',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        }
    };

    const handleQuery = async () => {
        if (!query.trim() || !selectedAgent || !provider) return;

        setIsLoading(true);
        setResponse(null);

        try {
            const result = await queryAgent(
                {
                    query: query.trim(),
                    agent_id: selectedAgent.agent_id
                },
                address ?? '',
                provider
            );
            setResponse(result);
        } catch (error) {
            console.error('Error processing query:', error);
            toast({
                title: 'Error',
                description: 'Failed to process query',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        } finally {
            setIsLoading(false);
        }
    };

    const formatHash = (hash: string | undefined) => {
        if (!hash) return '';
        return `${hash.slice(0, 6)}...${hash.slice(-4)}`;
    };

    const markdownComponents: Components = {
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
                    bg={codeBgColor}
                    borderRadius="md"
                    overflowX="auto"
                    whiteSpace="pre-wrap"
                    fontSize="sm"
                    fontFamily="mono"
                    border="1px solid"
                    borderColor={codeBorderColor}
                >
                    <Text color={codeTextColor}>{children}</Text>
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
            <Link href={href} color={linkColor} isExternal>
                {children}
            </Link>
        ),
    };

    return (
        <Box maxW="1200px" mx="auto" p={4} minH="100vh">
            <VStack spacing={8} align="stretch">
                {/* Header */}
                <HStack justify="space-between" bg={headerBgColor} p={4} borderRadius="lg">
                    <Text fontSize="2xl" fontWeight="bold" color={textColor}>
                        NeuroSpace Agents
                    </Text>
                    <Button
                        colorScheme={isConnected ? "green" : "blue"}
                        onClick={connect}
                    >
                        {isConnected ? `Connected: ${address?.slice(0, 6)}...${address?.slice(-4)}` : "Connect Wallet"}
                    </Button>
                </HStack>

                {/* Agents List */}
                <Box
                    p={6}
                    bg={cardBgColor}
                    borderRadius="lg"
                    borderWidth="1px"
                    borderColor={borderColor}
                >
                    <VStack spacing={4} align="stretch">
                        <Text fontSize="lg" fontWeight="semibold" color={textColor}>Available Agents</Text>
                        {agents.map(agent => (
                            <Box
                                key={agent.agent_id}
                                p={4}
                                bg={agentCardBgColor}
                                borderRadius="md"
                                borderWidth="1px"
                                cursor="pointer"
                                onClick={() => setSelectedAgent(agent)}
                                _hover={{ borderColor: 'blue.500' }}
                                borderColor={selectedAgent?.agent_id === agent.agent_id ? 'blue.500' : borderColor}
                            >
                                <VStack align="stretch" spacing={2}>
                                    <HStack justify="space-between">
                                        <Text fontSize="lg" fontWeight="semibold" color={textColor}>
                                            {agent.display_name}
                                        </Text>
                                        <Badge colorScheme={agent.is_available ? 'green' : 'red'}>
                                            {agent.is_available ? 'Available' : 'Unavailable'}
                                        </Badge>
                                    </HStack>
                                    <Text color={textColor}>{agent.description}</Text>
                                    <HStack wrap="wrap" spacing={2}>
                                        {agent.capabilities.map((capability, index) => (
                                            <Badge key={index} colorScheme="blue">
                                                {capability}
                                            </Badge>
                                        ))}
                                    </HStack>
                                    {agent.example_queries.length > 0 && (
                                        <Accordion allowToggle>
                                            <AccordionItem border="none">
                                                <AccordionButton px={0}>
                                                    <Box flex="1" textAlign="left">
                                                        <Text color={linkColor}>Example Queries</Text>
                                                    </Box>
                                                    <AccordionIcon />
                                                </AccordionButton>
                                                <AccordionPanel pb={4}>
                                                    <VStack align="stretch" spacing={2}>
                                                        {agent.example_queries.map((example, index) => (
                                                            <Text
                                                                key={index}
                                                                color={textColor}
                                                                cursor="pointer"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setQuery(example);
                                                                    setSelectedAgent(agent);
                                                                }}
                                                                _hover={{ color: 'blue.500' }}
                                                            >
                                                                {example}
                                                            </Text>
                                                        ))}
                                                    </VStack>
                                                </AccordionPanel>
                                            </AccordionItem>
                                        </Accordion>
                                    )}
                                </VStack>
                            </Box>
                        ))}
                    </VStack>
                </Box>

                {/* Query Section */}
                {selectedAgent && (
                    <Box
                        p={6}
                        bg={cardBgColor}
                        borderRadius="lg"
                        borderWidth="1px"
                        borderColor={borderColor}
                    >
                        <VStack spacing={4} align="stretch">
                            <Text fontSize="lg" fontWeight="semibold" color={textColor}>
                                Query {selectedAgent.display_name}
                            </Text>
                            <Textarea
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Enter your question here..."
                                size="lg"
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        handleQuery();
                                    }
                                }}
                            />
                            <Button
                                colorScheme="blue"
                                onClick={handleQuery}
                                isLoading={isLoading}
                                loadingText="Processing..."
                                isDisabled={!selectedAgent.is_available}
                            >
                                Submit
                            </Button>
                        </VStack>
                    </Box>
                )}

                {/* Response Section */}
                {response && (
                    <Box
                        p={6}
                        bg={cardBgColor}
                        borderRadius="lg"
                        borderWidth="1px"
                        borderColor={borderColor}
                    >
                        <VStack spacing={4} align="stretch">
                            <Text fontSize="lg" fontWeight="semibold" color={textColor}>Response</Text>
                            <Box p={4} bg={responseBgColor} borderRadius="md">
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    rehypePlugins={[rehypeRaw]}
                                    components={markdownComponents}
                                >
                                    {response.answer}
                                </ReactMarkdown>
                            </Box>

                            {/* Trace Information */}
                            <Box p={4} bg={responseBgColor} borderRadius="md">
                                <VStack align="stretch" spacing={2}>
                                    <Text fontWeight="semibold" color={textColor}>Trace Information</Text>
                                    <HStack spacing={4}>
                                        <Tooltip label="View on IPFS">
                                            <Link
                                                href={`https://ipfs.io/ipfs/${response.ipfs_hash}`}
                                                isExternal
                                                color={linkColor}
                                                display="flex"
                                                alignItems="center"
                                                gap={1}
                                            >
                                                <FiHash />
                                                IPFS: {formatHash(response.ipfs_hash)}
                                            </Link>
                                        </Tooltip>
                                        <Tooltip label="View on BaseScan">
                                            <Link
                                                href={`${blockExplorerUrl}/tx/${response.commitment_hash}`}
                                                isExternal
                                                color={linkColor}
                                                display="flex"
                                                alignItems="center"
                                                gap={1}
                                            >
                                                <FiLink />
                                                Commitment: {formatHash(response.commitment_hash)}
                                            </Link>
                                        </Tooltip>
                                    </HStack>
                                </VStack>
                            </Box>

                            {/* Execution Steps */}
                            <Accordion allowToggle>
                                <AccordionItem border="none">
                                    <AccordionButton px={0}>
                                        <Box flex="1" textAlign="left">
                                            <Text color={linkColor}>Execution Steps</Text>
                                        </Box>
                                        <AccordionIcon />
                                    </AccordionButton>
                                    <AccordionPanel pb={4}>
                                        <VStack align="stretch" spacing={4}>
                                            {response.metadata.steps.map((step, index) => (
                                                <Box
                                                    key={step.step_id}
                                                    p={4}
                                                    bg={responseBgColor}
                                                    borderRadius="md"
                                                >
                                                    <VStack align="stretch" spacing={2}>
                                                        <HStack justify="space-between">
                                                            <Text fontWeight="semibold" color={textColor}>
                                                                Step {index + 1}: {step.action}
                                                            </Text>
                                                            <Text fontSize="sm" color="gray.500">
                                                                {new Date(step.timestamp).toLocaleString()}
                                                            </Text>
                                                        </HStack>
                                                        <Box>
                                                            <Text fontSize="sm" color="gray.500">Inputs:</Text>
                                                            <Code p={2} borderRadius="md" display="block">
                                                                {JSON.stringify(step.inputs, null, 2)}
                                                            </Code>
                                                        </Box>
                                                        <Box>
                                                            <Text fontSize="sm" color="gray.500">Outputs:</Text>
                                                            <Code p={2} borderRadius="md" display="block">
                                                                {JSON.stringify(step.outputs, null, 2)}
                                                            </Code>
                                                        </Box>
                                                    </VStack>
                                                </Box>
                                            ))}
                                        </VStack>
                                    </AccordionPanel>
                                </AccordionItem>
                            </Accordion>
                        </VStack>
                    </Box>
                )}
            </VStack>
        </Box>
    );
} 