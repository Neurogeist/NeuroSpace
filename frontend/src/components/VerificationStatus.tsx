import React from 'react';
import {
    Box,
    HStack,
    Text,
    Tooltip,
    useColorModeValue,
    Spinner
} from '@chakra-ui/react';
import { FiCheck, FiX, FiAlertTriangle } from 'react-icons/fi';
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
    const textColor = useColorModeValue('gray.700', 'gray.300');
    const successColor = useColorModeValue('green.500', 'green.300');
    const warningColor = useColorModeValue('yellow.500', 'yellow.300');
    const errorColor = useColorModeValue('red.500', 'red.300');

    if (isLoading) {
        return (
            <HStack spacing={2} mt={2}>
                <Spinner size="sm" />
                <Text fontSize="xs" color={textColor}>Verifying...</Text>
            </HStack>
        );
    }

    if (error) {
        return (
            <HStack spacing={2} mt={2}>
                <FiAlertTriangle color={errorColor} />
                <Text fontSize="xs" color={errorColor}>Verification failed</Text>
            </HStack>
        );
    }

    if (!verificationResult) {
        return null;
    }

    if (verificationResult.is_valid && verificationResult.match) {
        return (
            <Tooltip label={`Verified by ${verificationResult.recovered_address}`}>
                <HStack spacing={2} mt={2}>
                    <FiCheck color={successColor} />
                    <Text fontSize="xs" color={successColor}>Verified</Text>
                </HStack>
            </Tooltip>
        );
    }

    if (verificationResult.is_valid && !verificationResult.match) {
        return (
            <Tooltip label={`Signature valid but signer (${verificationResult.recovered_address}) doesn't match expected address`}>
                <HStack spacing={2} mt={2}>
                    <FiAlertTriangle color={warningColor} />
                    <Text fontSize="xs" color={warningColor}>Invalid Signer</Text>
                </HStack>
            </Tooltip>
        );
    }

    return (
        <HStack spacing={2} mt={2}>
            <FiX color={errorColor} />
            <Text fontSize="xs" color={errorColor}>Invalid Signature</Text>
        </HStack>
    );
} 