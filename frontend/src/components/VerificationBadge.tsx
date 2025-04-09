import React, { useState, useEffect } from 'react';
import {
    Box,
    HStack,
    VStack,
    Text,
    Link,
    IconButton,
    Tooltip,
    useColorModeValue,
    Collapse,
    Button,
    useClipboard,
    useToast
} from '@chakra-ui/react';
import { FiCheck, FiX, FiRefreshCw, FiCopy, FiExternalLink } from 'react-icons/fi';
import axios from 'axios';

interface VerificationBadgeProps {
    verification_hash: string;
    signature: string;
    ipfs_cid: string;
    transaction_hash: string;
}

interface VerificationResponse {
    exists: boolean;
    submitter_address?: string;
    timestamp?: string;
}

export default function VerificationBadge({
    verification_hash,
    signature,
    ipfs_cid,
    transaction_hash
}: VerificationBadgeProps) {
    const [isVerified, setIsVerified] = useState<boolean | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [showDetails, setShowDetails] = useState(false);
    const [verificationData, setVerificationData] = useState<VerificationResponse | null>(null);
    const { hasCopied: hasCopiedHash, onCopy: onCopyHash } = useClipboard(verification_hash);
    const { hasCopied: hasCopiedSignature, onCopy: onCopySignature } = useClipboard(signature);
    const toast = useToast();

    const bgColor = useColorModeValue('gray.50', 'gray.700');
    const borderColor = useColorModeValue('gray.200', 'gray.600');
    const textColor = useColorModeValue('gray.700', 'gray.300');
    const linkColor = useColorModeValue('blue.500', 'blue.300');

    useEffect(() => {
        verifyHash();
    }, [verification_hash]);

    const verifyHash = async () => {
        try {
            setIsLoading(true);
            const response = await axios.get(`/verify/hash/${verification_hash}`);
            setVerificationData(response.data);
            setIsVerified(response.data.exists);
        } catch (error) {
            console.error('Error verifying hash:', error);
            setIsVerified(false);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCopy = (value: string, type: string) => {
        if (type === 'hash') {
            onCopyHash();
        } else {
            onCopySignature();
        }
        toast({
            title: 'Copied to clipboard',
            status: 'success',
            duration: 2000,
            isClosable: true,
        });
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
                        <Text fontSize="sm" color={textColor}>Verifying...</Text>
                    ) : (
                        <>
                            {isVerified ? (
                                <HStack>
                                    <FiCheck color="green" />
                                    <Text fontSize="sm" color="green.500">Verified</Text>
                                </HStack>
                            ) : (
                                <HStack>
                                    <FiX color="red" />
                                    <Text fontSize="sm" color="red.500">Not Verified</Text>
                                </HStack>
                            )}
                        </>
                    )}
                </HStack>
                <HStack>
                    <IconButton
                        aria-label="Refresh verification"
                        icon={<FiRefreshCw />}
                        size="xs"
                        variant="ghost"
                        onClick={verifyHash}
                        isLoading={isLoading}
                    />
                    <Button
                        size="xs"
                        variant="ghost"
                        onClick={() => setShowDetails(!showDetails)}
                    >
                        {showDetails ? 'Hide Details' : 'Show Details'}
                    </Button>
                </HStack>
            </HStack>

            <Collapse in={showDetails}>
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
                                onClick={() => handleCopy(verification_hash, 'hash')}
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
                                onClick={() => handleCopy(signature, 'signature')}
                            />
                        </HStack>
                    </Box>

                    {verificationData?.exists && (
                        <Box>
                            <Text fontSize="xs" fontWeight="bold" color={textColor}>Submitted by</Text>
                            <Text fontSize="xs" color={textColor}>
                                {verificationData.submitter_address}
                            </Text>
                            <Text fontSize="xs" color={textColor}>
                                {new Date(verificationData.timestamp || '').toLocaleString()}
                            </Text>
                        </Box>
                    )}

                    <HStack spacing={2}>
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
                    </HStack>
                </VStack>
            </Collapse>
        </Box>
    );
} 