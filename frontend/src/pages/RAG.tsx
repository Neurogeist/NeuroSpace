import React, { useState, useEffect } from 'react';
import {
    Box,
    VStack,
    HStack,
    Text,
    Button,
    Input,
    useToast,
    useColorModeValue,
    Divider,
    Spinner,
    Link,
    Tooltip,
    IconButton,
    Textarea,
    Badge,
    Code,
    useBreakpointValue
} from '@chakra-ui/react';
import { FiUpload, FiLink, FiHash } from 'react-icons/fi';
import { uploadDocument, queryDocuments, getDocuments, verifyRAGResponse } from '../services/rag';
import { Document, Source, RAGResponse } from '../services/rag';

export default function RAGPage() {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploadStatus, setUploadStatus] = useState<string>('');
    const [query, setQuery] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [response, setResponse] = useState<string>('');
    const [sources, setSources] = useState<Source[]>([]);
    const [documents, setDocuments] = useState<Document[]>([]);
    const [verificationResult, setVerificationResult] = useState<boolean | null>(null);
    const toast = useToast();

    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const textColor = useColorModeValue('gray.800', 'gray.100');
    const linkColor = useColorModeValue('blue.500', 'blue.300');

    const blockExplorerUrl = import.meta.env.VITE_ENVIRONMENT?.toLowerCase() === 'production'
        ? 'https://basescan.org'
        : 'https://sepolia.basescan.org';

    useEffect(() => {
        loadDocuments();
    }, []);

    const loadDocuments = async () => {
        try {
            const docs = await getDocuments();
            setDocuments(docs);
        } catch (error) {
            console.error('Error loading documents:', error);
            toast({
                title: 'Error',
                description: 'Failed to load documents',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        }
    };

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setSelectedFile(file);
        setUploadStatus('Uploading...');

        try {
            const result = await uploadDocument(file);
            setUploadStatus('Uploaded');
            setDocuments(prev => [...prev, result]);
            toast({
                title: 'Success',
                description: 'Document uploaded successfully',
                status: 'success',
                duration: 3000,
                isClosable: true,
            });
        } catch (error) {
            setUploadStatus('Failed');
            toast({
                title: 'Error',
                description: 'Failed to upload document',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        }
    };

    const handleQuery = async () => {
        if (!query.trim()) return;

        setIsLoading(true);
        try {
            const result = await queryDocuments(query);
            setResponse(result.response);
            setSources(result.sources);

            // Verify the response
            const verified = await verifyRAGResponse(
                result.verification_hash,
                result.signature
            );
            setVerificationResult(verified);

            if (!verified) {
                toast({
                    title: 'Warning',
                    description: 'Response verification failed',
                    status: 'warning',
                    duration: 3000,
                    isClosable: true,
                });
            }
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

    return (
        <Box maxW="1200px" mx="auto" p={4}>
            <VStack spacing={8} align="stretch">
                {/* Header */}
                <Text fontSize="2xl" fontWeight="bold" textAlign="center">
                    NeuroSpace Document Q&A
                </Text>

                {/* Upload Section */}
                <Box
                    p={6}
                    bg={bgColor}
                    borderRadius="lg"
                    borderWidth="1px"
                    borderColor={borderColor}
                >
                    <VStack spacing={4} align="stretch">
                        <Text fontSize="lg" fontWeight="semibold">Upload Documents</Text>
                        <HStack>
                            <Input
                                type="file"
                                accept=".pdf,.txt"
                                onChange={handleFileUpload}
                                display="none"
                                id="file-upload"
                            />
                            <Button
                                as="label"
                                htmlFor="file-upload"
                                leftIcon={<FiUpload />}
                                colorScheme="blue"
                            >
                                Choose File
                            </Button>
                            {selectedFile && (
                                <Text>{selectedFile.name}</Text>
                            )}
                            {uploadStatus && (
                                <Badge colorScheme={uploadStatus === 'Uploaded' ? 'green' : 'blue'}>
                                    {uploadStatus}
                                </Badge>
                            )}
                        </HStack>
                    </VStack>
                </Box>

                {/* Document List */}
                <Box
                    p={6}
                    bg={bgColor}
                    borderRadius="lg"
                    borderWidth="1px"
                    borderColor={borderColor}
                >
                    <VStack spacing={4} align="stretch">
                        <Text fontSize="lg" fontWeight="semibold">Uploaded Documents</Text>
                        {documents.map(doc => (
                            <HStack key={doc.id} justify="space-between" p={2} bg={useColorModeValue('gray.50', 'gray.700')} borderRadius="md">
                                <Text>{doc.name}</Text>
                                <HStack>
                                    <Tooltip label="View on IPFS">
                                        <Link
                                            href={`https://ipfs.io/ipfs/${doc.ipfsHash}`}
                                            isExternal
                                            color={linkColor}
                                        >
                                            <IconButton
                                                aria-label="View on IPFS"
                                                icon={<FiHash />}
                                                size="sm"
                                                variant="ghost"
                                            />
                                        </Link>
                                    </Tooltip>
                                </HStack>
                            </HStack>
                        ))}
                    </VStack>
                </Box>

                {/* Query Section */}
                <Box
                    p={6}
                    bg={bgColor}
                    borderRadius="lg"
                    borderWidth="1px"
                    borderColor={borderColor}
                >
                    <VStack spacing={4} align="stretch">
                        <Text fontSize="lg" fontWeight="semibold">Ask a Question</Text>
                        <Textarea
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Enter your question here..."
                            size="lg"
                        />
                        <Button
                            colorScheme="blue"
                            onClick={handleQuery}
                            isLoading={isLoading}
                            loadingText="Processing..."
                        >
                            Submit
                        </Button>
                    </VStack>
                </Box>

                {/* Response Section */}
                {response && (
                    <Box
                        p={6}
                        bg={bgColor}
                        borderRadius="lg"
                        borderWidth="1px"
                        borderColor={borderColor}
                    >
                        <VStack spacing={4} align="stretch">
                            <HStack justify="space-between">
                                <Text fontSize="lg" fontWeight="semibold">Response</Text>
                                {verificationResult !== null && (
                                    <Badge colorScheme={verificationResult ? 'green' : 'red'}>
                                        {verificationResult ? 'Verified' : 'Unverified'}
                                    </Badge>
                                )}
                            </HStack>
                            <Box p={4} bg={useColorModeValue('gray.50', 'gray.700')} borderRadius="md">
                                <Text>{response}</Text>
                            </Box>
                        </VStack>
                    </Box>
                )}

                {/* Sources Section */}
                {sources.length > 0 && (
                    <Box
                        p={6}
                        bg={bgColor}
                        borderRadius="lg"
                        borderWidth="1px"
                        borderColor={borderColor}
                    >
                        <VStack spacing={4} align="stretch">
                            <Text fontSize="lg" fontWeight="semibold">Sources</Text>
                            {sources.map(source => (
                                <Box
                                    key={source.id}
                                    p={4}
                                    bg={useColorModeValue('gray.50', 'gray.700')}
                                    borderRadius="md"
                                >
                                    <VStack align="stretch" spacing={2}>
                                        <Text>{source.snippet}</Text>
                                        <HStack spacing={4}>
                                            <Tooltip label="View on IPFS">
                                                <Link
                                                    href={`https://ipfs.io/ipfs/${source.ipfsHash}`}
                                                    isExternal
                                                    color={linkColor}
                                                    display="flex"
                                                    alignItems="center"
                                                    gap={1}
                                                >
                                                    <FiHash />
                                                    {formatHash(source.ipfsHash)}
                                                </Link>
                                            </Tooltip>
                                            {source.transaction_hash && (
                                                <Tooltip label="View on BaseScan">
                                                    <Link
                                                        href={`${blockExplorerUrl}/tx/${source.transaction_hash}`}
                                                        isExternal
                                                        color={linkColor}
                                                        display="flex"
                                                        alignItems="center"
                                                        gap={1}
                                                    >
                                                        <FiLink />
                                                        {formatHash(source.transaction_hash)}
                                                    </Link>
                                                </Tooltip>
                                            )}
                                        </HStack>
                                    </VStack>
                                </Box>
                            ))}
                        </VStack>
                    </Box>
                )}
            </VStack>
        </Box>
    );
} 