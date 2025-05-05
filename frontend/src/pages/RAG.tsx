import React, { useState, useEffect, useRef, useCallback } from 'react';
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
    useBreakpointValue,
    AlertDialog,
    AlertDialogBody,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogContent,
    AlertDialogOverlay,
    Container,
    Alert,
    AlertIcon,
    Flex,
    Heading,
} from '@chakra-ui/react';
import { FiUpload, FiLink, FiHash, FiTrash2 } from 'react-icons/fi';
import { uploadDocument, queryDocuments, getDocuments, verifyRAGResponse, deleteDocument } from '../services/rag';
import { connectWallet, getNetworkInfo } from '../services/blockchain';

export default function RAGPage() {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploadStatus, setUploadStatus] = useState<string>('');
    const [query, setQuery] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [response, setResponse] = useState<string>('');
    const [sources, setSources] = useState<any[]>([]);
    const [documents, setDocuments] = useState<any[]>([]);
    const [verificationResult, setVerificationResult] = useState<boolean | null>(null);
    const [isDeleteAlertOpen, setIsDeleteAlertOpen] = useState(false);
    const [documentToDelete, setDocumentToDelete] = useState<string | null>(null);
    const cancelRef = useRef<HTMLButtonElement>(null);
    const toast = useToast();
    const [walletAddress, setWalletAddress] = useState<string | null>(null);
    const [isConnecting, setIsConnecting] = useState(false);
    const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);

    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const textColor = useColorModeValue('gray.800', 'gray.100');
    const linkColor = useColorModeValue('blue.500', 'blue.300');

    const blockExplorerUrl = import.meta.env.VITE_ENVIRONMENT?.toLowerCase() === 'production'
        ? 'https://basescan.org'
        : 'https://sepolia.basescan.org';

    const handleConnectWallet = async () => {
        try {
            setIsConnecting(true);
            const address = await connectWallet();
            setWalletAddress(address);
            toast({
                title: 'Wallet Connected',
                description: `Connected to ${address.slice(0, 6)}...${address.slice(-4)}`,
                status: 'success',
                duration: 3000,
                isClosable: true,
            });
        } catch (error) {
            console.error('Error connecting wallet:', error);
            toast({
                title: 'Error',
                description: 'Failed to connect wallet. Please make sure MetaMask is installed and try again.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsConnecting(false);
        }
    };

    const loadDocuments = useCallback(async () => {
        if (!walletAddress) return;
        
        try {
            setIsLoadingDocuments(true);
            const docs = await getDocuments(walletAddress);
            setDocuments(docs);
        } catch (error) {
            console.error('Error loading documents:', error);
            toast({
                title: 'Error',
                description: 'Failed to load documents. Please try again.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsLoadingDocuments(false);
        }
    }, [walletAddress, toast]);

    useEffect(() => {
        loadDocuments();
    }, [loadDocuments]);

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!walletAddress) {
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
            const result = await uploadDocument(file, walletAddress);
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
        // Clear previous response and sources
        setResponse('');
        setSources([]);
        setVerificationResult(null);

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

    const handleDeleteClick = (documentId: string) => {
        setDocumentToDelete(documentId);
        setIsDeleteAlertOpen(true);
    };

    const handleDeleteConfirm = async () => {
        if (!documentToDelete || !walletAddress) return;

        try {
            await deleteDocument(documentToDelete, walletAddress);
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

    return (
        <Container maxW="container.xl" py={8}>
            <VStack spacing={8} align="stretch">
                <Heading size="lg">RAG Interface</Heading>
                
                {!walletAddress ? (
                    <Alert status="info">
                        <AlertIcon />
                        Please connect your wallet to upload and query documents.
                    </Alert>
                ) : (
                    <>
                        <Box>
                            <Heading size="md" mb={4}>Upload Document</Heading>
                            <Input
                                type="file"
                                accept=".txt,.pdf"
                                onChange={handleFileUpload}
                                isDisabled={isLoading}
                            />
                        </Box>

                        <Box>
                            <Heading size="md" mb={4}>Your Documents</Heading>
                            {isLoadingDocuments ? (
                                <Spinner />
                            ) : documents.length === 0 ? (
                                <Text>No documents uploaded yet.</Text>
                            ) : (
                                <VStack align="stretch" spacing={2}>
                                    {documents.map((doc) => (
                                        <Flex
                                            key={doc.id}
                                            justify="space-between"
                                            align="center"
                                            p={2}
                                            borderWidth={1}
                                            borderRadius="md"
                                        >
                                            <Text>{doc.name}</Text>
                                            <HStack>
                                                <Tooltip label="View on IPFS">
                                                    <Link
                                                        href={`https://ipfs.io/ipfs/${doc.ipfsHash}`}
                                                        isExternal
                                                    >
                                                        <IconButton
                                                            aria-label="View on IPFS"
                                                            icon={<FiLink />}
                                                            size="sm"
                                                        />
                                                    </Link>
                                                </Tooltip>
                                                <Tooltip label="Delete document">
                                                    <IconButton
                                                        aria-label="Delete document"
                                                        icon={<FiTrash2 />}
                                                        colorScheme="red"
                                                        size="sm"
                                                        onClick={() => handleDeleteClick(doc.id)}
                                                    />
                                                </Tooltip>
                                            </HStack>
                                        </Flex>
                                    ))}
                                </VStack>
                            )}
                        </Box>

                        <Box>
                            <Heading size="md" mb={4}>Ask a Question</Heading>
                            <VStack spacing={4}>
                                <Textarea
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder="Enter your question here..."
                                    size="lg"
                                    isDisabled={isLoading}
                                />
                                <Button
                                    colorScheme="blue"
                                    onClick={handleQuery}
                                    isLoading={isLoading}
                                    loadingText="Processing..."
                                >
                                    Submit Query
                                </Button>
                            </VStack>
                        </Box>

                        {response && (
                            <Box>
                                <Heading size="md" mb={4}>Response</Heading>
                                <VStack spacing={4} align="stretch">
                                    <Text>{response}</Text>
                                    <HStack>
                                        <Button
                                            size="sm"
                                            onClick={handleQuery}
                                            isLoading={isLoading}
                                            loadingText="Verifying..."
                                        >
                                            Verify Response
                                        </Button>
                                        {verificationResult !== null && (
                                            <Badge
                                                colorScheme={verificationResult ? "green" : "red"}
                                            >
                                                {verificationResult ? "Verified" : "Not Verified"}
                                            </Badge>
                                        )}
                                    </HStack>
                                </VStack>
                            </Box>
                        )}

                        {sources.length > 0 && (
                            <Box>
                                <Heading size="md" mb={4}>Sources</Heading>
                                <VStack spacing={4} align="stretch">
                                    {sources.map((source, index) => (
                                        <Box
                                            key={index}
                                            p={4}
                                            borderWidth={1}
                                            borderRadius="md"
                                        >
                                            <Text mb={2}>{source.snippet}</Text>
                                            <HStack spacing={4}>
                                                <Tooltip label="View on IPFS">
                                                    <Link
                                                        href={`https://ipfs.io/ipfs/${source.ipfsHash}`}
                                                        isExternal
                                                    >
                                                        <IconButton
                                                            aria-label="View on IPFS"
                                                            icon={<FiLink />}
                                                            size="sm"
                                                        />
                                                    </Link>
                                                </Tooltip>
                                                {source.transaction_hash && (
                                                    <Tooltip label="View on Blockchain">
                                                        <Link
                                                            href={`${getNetworkInfo().explorerUrl}/tx/${source.transaction_hash}`}
                                                            isExternal
                                                        >
                                                            <IconButton
                                                                aria-label="View on Blockchain"
                                                                icon={<FiHash />}
                                                                size="sm"
                                                            />
                                                        </Link>
                                                    </Tooltip>
                                                )}
                                            </HStack>
                                        </Box>
                                    ))}
                                </VStack>
                            </Box>
                        )}
                    </>
                )}

                {!walletAddress && (
                    <Button
                        colorScheme="blue"
                        onClick={handleConnectWallet}
                        isLoading={isConnecting}
                        loadingText="Connecting..."
                    >
                        Connect Wallet
                    </Button>
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
        </Container>
    );
} 