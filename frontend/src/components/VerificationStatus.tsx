import {
    Box,
    HStack,
    Text,
    Tooltip,
    useColorModeValue
} from '@chakra-ui/react';
import { VerificationResponse } from '../services/api';

interface VerificationStatusProps {
    verificationResult: VerificationResponse | null;
    isLoading: boolean;
    error?: string;
}

export default function VerificationStatus({
    verificationResult,
    isLoading,
    error
}: VerificationStatusProps) {
    const statusColor = useColorModeValue('gray.600', 'gray.300');
    const verifiedColor = useColorModeValue('green.600', 'green.300');
    const invalidColor = useColorModeValue('red.600', 'red.300');
    const warningColor = useColorModeValue('yellow.600', 'yellow.300');

    if (isLoading) {
        return (
            <Box mt={2} fontSize="sm" color={statusColor}>
                <HStack spacing={2}>
                    <Text>⏳ Verifying...</Text>
                </HStack>
            </Box>
        );
    }

    if (error) {
        return (
            <Box mt={2} fontSize="sm" color={invalidColor}>
                <HStack spacing={2}>
                    <Text>❌ Verification Error</Text>
                </HStack>
            </Box>
        );
    }

    if (!verificationResult) {
        return null;
    }

    if (!verificationResult.is_valid) {
        return (
            <Box mt={2} fontSize="sm" color={invalidColor}>
                <HStack spacing={2}>
                    <Text>❌ Invalid Signature</Text>
                </HStack>
            </Box>
        );
    }

    if (!verificationResult.match) {
        return (
            <Box mt={2} fontSize="sm" color={warningColor}>
                <HStack spacing={2}>
                    <Text>⚠️ Signature Mismatch</Text>
                    <Tooltip label="Expected address does not match recovered address">
                        <Text fontSize="xs" color={statusColor}>
                            (Expected: {verificationResult.expected_address?.slice(0, 6)}...{verificationResult.expected_address?.slice(-4)})
                        </Text>
                    </Tooltip>
                </HStack>
            </Box>
        );
    }

    return (
        <Box mt={2} fontSize="sm" color={verifiedColor}>
            <HStack spacing={2}>
                <Text>✅ Verified</Text>
                <Tooltip label="Recovered address matches expected address">
                    <Text fontSize="xs" color={statusColor}>
                        ({verificationResult.recovered_address.slice(0, 6)}...{verificationResult.recovered_address.slice(-4)})
                    </Text>
                </Tooltip>
            </HStack>
        </Box>
    );
} 