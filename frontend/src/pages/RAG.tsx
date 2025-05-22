import React, { useState, useEffect, useRef } from 'react';
import {
    Box,
    VStack,
    HStack,
    Text,
    Button,
    Input,
    useToast,
    useColorModeValue,
    Link,
    Tooltip,
    IconButton,
    Textarea,
    Badge,
    AlertDialog,
    AlertDialogBody,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogContent,
    AlertDialogOverlay,
    Code,
} from '@chakra-ui/react';
import { FiUpload, FiLink, FiHash, FiTrash2 } from 'react-icons/fi';
import { uploadDocument, queryDocuments, getDocuments, verifyRAGResponse, deleteDocument } from '../services/rag';
import { Document, Source } from '../services/rag';
import { useWallet } from '../hooks/useWallet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Components } from 'react-markdown';
import { verifyHash } from '../utils/verification';

export default function RAGPage() {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploadStatus, setUploadStatus] = useState<string>('');
    const [query, setQuery] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [response, setResponse] = useState<string>('');
    const [sources, setSources] = useState<Source[]>([]);
    const [documents, setDocuments] = useState<Document[]>([]);
    const [verificationResult, setVerificationResult] = useState<boolean | null>(null);
    const [isDeleteAlertOpen, setIsDeleteAlertOpen] = useState(false);
    const [documentToDelete, setDocumentToDelete] = useState<string | null>(null);
    const cancelRef = useRef<HTMLButtonElement>(null);
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
    const documentBgColor = useColorModeValue('gray.50', 'gray.700');
    const responseBgColor = useColorModeValue('gray.50', 'gray.700');
    const sourceBgColor = useColorModeValue('gray.50', 'gray.700');

    const blockExplorerUrl = import.meta.env.VITE_ENVIRONMENT?.toLowerCase() === 'production'
        ? 'https://basescan.org'
        : 'https://sepolia.basescan.org';

    useEffect(() => {
        if (isConnected && address) {
            loadDocuments(address);
        }
    }, [isConnected, address]);

    const loadDocuments = async (walletAddress: string) => {
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
            const docs = await getDocuments(walletAddress, provider);
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

        if (!isConnected || !address || !provider) {
            toast({
                title: 'Wallet Required',
                description: 'Please connect your wallet to upload documents',
                status: 'warning',
                duration: 3000,
                isClosable: true,
            });
            return;
        }

        setSelectedFile(file);
        setUploadStatus('Uploading...');

        try {
            const result = await uploadDocument(file, address, provider);
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
        if (!query.trim() || !provider) return;

        setIsLoading(true);
        setResponse('');
        setSources([]);
        setVerificationResult(null);

        try {
            const result = await queryDocuments(query, address || '', provider);
            setResponse(result.response);
            setSources(result.sources);

            // Create verification data matching backend payload
            const verificationData = {
                prompt: query,
                response: result.response,
                model_name: "mixtral-8x7b-instruct",
                model_id: "mixtral-8x7b-instruct",
                temperature: 0.7,
                max_tokens: 1000,
                system_prompt: null,
                timestamp: new Date().toISOString().replace(/\.\d{3}Z$/, ''), // Remove milliseconds and Z
                wallet_address: address || '',
                session_id: '',
                rag_sources: result.sources.map(source => ({
                    id: source.id,
                    snippet: source.snippet,
                    ipfsHash: source.ipfsHash,
                    chunk_index: source.chunk_index,
                    similarity: source.similarity
                })),
                tool_calls: []
            };

            // First verify the hash
            const hashIsValid = await verifyHash(verificationData, result.verification_hash);
            if (!hashIsValid) {
                console.error('Hash verification failed');
                setVerificationResult(false);
                toast({
                    title: 'Warning',
                    description: 'Response verification failed - hash mismatch',
                    status: 'warning',
                    duration: 3000,
                    isClosable: true,
                });
                return;
            }

            // Then verify the signature
            const verified = await verifyRAGResponse(
                result.verification_hash,
                result.signature
            );
            setVerificationResult(verified);

            if (!verified) {
                toast({
                    title: 'Warning',
                    description: 'Response verification failed - signature mismatch',
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

    const handleDeleteClick = (documentId: string) => {
        setDocumentToDelete(documentId);
        setIsDeleteAlertOpen(true);
    };

    const handleDeleteConfirm = async () => {
        if (!documentToDelete || !address || !provider) return;

        try {
            await deleteDocument(documentToDelete, address, provider);
            setDocuments(documents.filter(doc => doc.id !== documentToDelete));
            toast({
                title: 'Success',
                description: 'Document deleted successfully',
                status: 'success',
                duration: 3000,
                isClosable: true,
            });
        } catch (error) {
            console.error('Error deleting document:', error);
            toast({
                title: 'Error',
                description: 'Failed to delete document',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        } finally {
            setIsDeleteAlertOpen(false);
            setDocumentToDelete(null);
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
                        NeuroSpace Document Q&A
                    </Text>
                    <Button
                        colorScheme={isConnected ? "green" : "blue"}
                        onClick={connect}
                    >
                        {isConnected ? `Connected: ${address?.slice(0, 6)}...${address?.slice(-4)}` : "Connect Wallet"}
                    </Button>
                </HStack>

                {/* Upload Section */}
                <Box
                    p={6}
                    bg={cardBgColor}
                    borderRadius="lg"
                    borderWidth="1px"
                    borderColor={borderColor}
                    shadow="md"
                >
                    <VStack spacing={4} align="stretch">
                        <Text fontSize="lg" fontWeight="semibold" color={textColor}>Upload Documents</Text>
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
                                isDisabled={!isConnected}
                            >
                                Choose File
                            </Button>
                            {selectedFile && (
                                <Text color={textColor}>{selectedFile.name}</Text>
                            )}
                            {uploadStatus && (
                                <Badge colorScheme={uploadStatus === 'Uploaded' ? 'green' : 'blue'}>
                                    {uploadStatus}
                                </Badge>
                            )}
                        </HStack>
                        {!isConnected && (
                            <Text color="orange.500" fontSize="sm">
                                Please connect your wallet to upload documents
                            </Text>
                        )}
                    </VStack>
                </Box>

                {/* Document List */}
                <Box
                    p={6}
                    bg={cardBgColor}
                    borderRadius="lg"
                    borderWidth="1px"
                    borderColor={borderColor}
                >
                    <VStack spacing={4} align="stretch">
                        <Text fontSize="lg" fontWeight="semibold" color={textColor}>Uploaded Documents</Text>
                        {documents.map(doc => (
                            <HStack key={doc.id} justify="space-between" p={2} bg={documentBgColor} borderRadius="md">
                                <Text color={textColor}>{doc.name}</Text>
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
                                    <Tooltip label="Delete document">
                                        <IconButton
                                            aria-label="Delete document"
                                            icon={<FiTrash2 />}
                                            size="sm"
                                            variant="ghost"
                                            colorScheme="red"
                                            onClick={() => handleDeleteClick(doc.id)}
                                        />
                                    </Tooltip>
                                </HStack>
                            </HStack>
                        ))}
                    </VStack>
                </Box>

                {/* Query Section */}
                <Box
                    p={6}
                    bg={cardBgColor}
                    borderRadius="lg"
                    borderWidth="1px"
                    borderColor={borderColor}
                >
                    <VStack spacing={4} align="stretch">
                        <Text fontSize="lg" fontWeight="semibold" color={textColor}>Ask a Question</Text>
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
                        bg={cardBgColor}
                        borderRadius="lg"
                        borderWidth="1px"
                        borderColor={borderColor}
                    >
                        <VStack spacing={4} align="stretch">
                            <HStack justify="space-between">
                                <Text fontSize="lg" fontWeight="semibold" color={textColor}>Response</Text>
                                {verificationResult !== null && (
                                    <Badge colorScheme={verificationResult ? 'green' : 'red'}>
                                        {verificationResult ? 'Verified' : 'Unverified'}
                                    </Badge>
                                )}
                            </HStack>
                            <Box p={4} bg={responseBgColor} borderRadius="md">
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    rehypePlugins={[rehypeRaw]}
                                    components={markdownComponents}
                                >
                                    {response}
                                </ReactMarkdown>
                            </Box>
                        </VStack>
                    </Box>
                )}

                {/* Sources Section */}
                {sources.length > 0 && (
                    <Box
                        p={6}
                        bg={cardBgColor}
                        borderRadius="lg"
                        borderWidth="1px"
                        borderColor={borderColor}
                    >
                        <VStack spacing={4} align="stretch">
                            <Text fontSize="lg" fontWeight="semibold" color={textColor}>Sources</Text>
                            {sources.map((source, index) => (
                                <Box
                                    key={`${source.id}-${index}`}
                                    p={4}
                                    bg={sourceBgColor}
                                    borderRadius="md"
                                >
                                    <VStack align="stretch" spacing={2}>
                                        <Text color={textColor}>{source.snippet}</Text>
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

            {/* Delete Confirmation Dialog */}
            <AlertDialog
                isOpen={isDeleteAlertOpen}
                leastDestructiveRef={cancelRef}
                onClose={() => setIsDeleteAlertOpen(false)}
            >
                <AlertDialogOverlay>
                    <AlertDialogContent>
                        <AlertDialogHeader fontSize="lg" fontWeight="bold">
                            Delete Document
                        </AlertDialogHeader>

                        <AlertDialogBody>
                            Are you sure you want to delete this document? This action cannot be undone.
                        </AlertDialogBody>

                        <AlertDialogFooter>
                            <Button ref={cancelRef} onClick={() => setIsDeleteAlertOpen(false)}>
                                Cancel
                            </Button>
                            <Button colorScheme="red" onClick={handleDeleteConfirm} ml={3}>
                                Delete
                            </Button>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialogOverlay>
            </AlertDialog>
        </Box>
    );
} 