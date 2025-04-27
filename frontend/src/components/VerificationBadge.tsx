import { useState, useRef } from 'react';
import {
    Box,
    HStack,
    VStack,
    Text,
    Link,
    IconButton,
    useColorModeValue,
    Collapse,
    Button,
    useClipboard,
    useToast,
    Spinner
} from '@chakra-ui/react';
import { FiRefreshCw, FiCopy, FiExternalLink } from 'react-icons/fi';
import { verifyMessage } from '../services/api';

interface VerificationBadgeProps {
    verification_hash: string;
    signature: string;
    ipfs_cid?: string;
    transaction_hash?: string;
}

// Cache for verification results
const verificationCache = new Map<string, {
    is_valid: boolean;
    recovered_address: string;
    expected_address?: string;
    match: boolean;
    timestamp: number;
}>();

// Cache expiration time (5 minutes)
const CACHE_EXPIRATION = 5 * 60 * 1000;

export default function VerificationBadge({
    verification_hash,
    signature,
    ipfs_cid,
    transaction_hash
}: VerificationBadgeProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const [verificationResult, setVerificationResult] = useState<{
        is_valid: boolean;
        recovered_address: string;
        expected_address?: string;
        match: boolean;
    } | null>(null);
    const [error, setError] = useState<string | null>(null);
    const { onCopy: onCopyHash } = useClipboard(verification_hash);
    const { onCopy: onCopySignature } = useClipboard(signature);
    const toast = useToast();
    const isVerifying = useRef(false);

    const bgColor = useColorModeValue('gray.50', 'gray.700');
    const borderColor = useColorModeValue('gray.200', 'gray.600');
    const textColor = useColorModeValue('gray.700', 'gray.300');
    const linkColor = useColorModeValue('blue.500', 'blue.300');

    const verifyHash = async () => {
        if (isVerifying.current) return;
        isVerifying.current = true;

        try {
            // Check cache first
            const cachedResult = verificationCache.get(verification_hash);
            if (cachedResult && Date.now() - cachedResult.timestamp < CACHE_EXPIRATION) {
                setVerificationResult(cachedResult);
                return;
            }

            setIsLoading(true);
            setError(null);
            const result = await verifyMessage(verification_hash, signature);
            
            // Update cache
            verificationCache.set(verification_hash, {
                ...result,
                timestamp: Date.now()
            });
            
            setVerificationResult(result);
        } catch (err) {
            console.error('Error verifying hash:', err);
            setError(err instanceof Error ? err.message : 'Failed to verify hash');
        } finally {
            setIsLoading(false);
            isVerifying.current = false;
        }
    };

    const handleCopy = (type: 'hash' | 'signature') => {
        if (type === 'hash') {
            onCopyHash();
            toast({
                title: "Copied",
                description: "Verification hash copied to clipboard",
                status: "success",
                duration: 2000,
                isClosable: true,
            });
        } else {
            onCopySignature();
            toast({
                title: "Copied",
                description: "Signature copied to clipboard",
                status: "success",
                duration: 2000,
                isClosable: true,
            });
        }
    };

    return (
        <Box
            mt={2}
            p={2}
            borderRadius="md"
            border="1px"
            borderColor={borderColor}
            bg={bgColor}
        >
            <HStack justify="space-between">
                <HStack>
                    {isLoading ? (
                        <HStack>
                            <Spinner size="sm" />
                            <Text fontSize="sm">Verifying...</Text>
                        </HStack>
                    ) : error ? (
                        <Text fontSize="sm" color="red.500">Error: {error}</Text>
                    ) : verificationResult ? (
                        <>
                            <Text fontSize="sm">
                                {verificationResult.is_valid && verificationResult.match ? (
                                    <span style={{ color: 'green' }}>✅ Verified</span>
                                ) : (
                                    <span style={{ color: 'red' }}>⚠️ Invalid</span>
                                )}
                            </Text>
                            <IconButton
                                aria-label="Refresh verification"
                                icon={<FiRefreshCw />}
                                size="xs"
                                onClick={verifyHash}
                                isLoading={isLoading}
                            />
                            <Button
                                size="xs"
                                onClick={() => setIsExpanded(!isExpanded)}
                            >
                                {isExpanded ? 'Hide Details' : 'Show Details'}
                            </Button>
                        </>
                    ) : null}
                </HStack>
            </HStack>

            <Collapse in={isExpanded}>
                <VStack align="stretch" mt={2} spacing={2}>
                    <Box>
                        <Text fontSize="xs" fontWeight="bold" color={textColor}>Verification Hash</Text>
                        <HStack>
                            <Text fontSize="xs" color={textColor} isTruncated>
                                {verification_hash}
                            </Text>
                            <IconButton
                                aria-label="Copy hash"
                                icon={<FiCopy />}
                                size="xs"
                                variant="ghost"
                                onClick={() => handleCopy('hash')}
                            />
                        </HStack>
                    </Box>

                    <Box>
                        <Text fontSize="xs" fontWeight="bold" color={textColor}>Signature</Text>
                        <HStack>
                            <Text fontSize="xs" color={textColor} isTruncated>
                                {signature}
                            </Text>
                            <IconButton
                                aria-label="Copy signature"
                                icon={<FiCopy />}
                                size="xs"
                                variant="ghost"
                                onClick={() => handleCopy('signature')}
                            />
                        </HStack>
                    </Box>

                    {verificationResult && (
                        <>
                            <Text fontSize="xs" fontWeight="bold" color={textColor}>Recovered Address</Text>
                            <Text fontSize="xs" color={textColor}>
                                {verificationResult.recovered_address}
                            </Text>
                            <Text fontSize="xs" fontWeight="bold" color={textColor}>Expected Address</Text>
                            <Text fontSize="xs" color={textColor}>
                                {verificationResult.expected_address}
                            </Text>
                            <Text fontSize="xs" fontWeight="bold" color={textColor}>Match</Text>
                            <Text fontSize="xs" color={textColor}>
                                {verificationResult.match ? '✅' : '❌'}
                            </Text>
                        </>
                    )}

                    <HStack spacing={2}>
                        {ipfs_cid && (
                            <Link
                                href={`https://ipfs.io/ipfs/${ipfs_cid}`}
                                isExternal
                                fontSize="xs"
                                color={linkColor}
                                display="flex"
                                alignItems="center"
                                gap={1}
                            >
                                <FiExternalLink />
                                View on IPFS
                            </Link>
                        )}
                        {transaction_hash && (
                            <Link
                                href={`https://sepolia.basescan.org/tx/${transaction_hash}`}
                                isExternal
                                fontSize="xs"
                                color={linkColor}
                                display="flex"
                                alignItems="center"
                                gap={1}
                            >
                                <FiExternalLink />
                                View on BaseScan
                            </Link>
                        )}
                    </HStack>
                </VStack>
            </Collapse>
        </Box>
    );
} 