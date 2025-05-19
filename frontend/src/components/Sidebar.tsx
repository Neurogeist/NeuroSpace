import React, { useState } from 'react';
import {
    Box,
    VStack,
    Button,
    Text,
    useColorModeValue,
    Divider,
    HStack,
    IconButton,
    Tooltip,
    useDisclosure,
    AlertDialog,
    AlertDialogBody,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogContent,
    AlertDialogOverlay,
    useToast,
    useBreakpointValue
} from '@chakra-ui/react';
import { FiPlus, FiTrash2 } from 'react-icons/fi';
import { ChatSession } from '../types/chat';
import { deleteSession } from '../services/api';
import { useApp } from '../context/AppContext';
import { ethers } from 'ethers';

interface SidebarProps {
    sessions: ChatSession[];
    activeSessionId: string | null;
    onNewChat: () => void;
    onSelectSession: (sessionId: string) => void;
    userAddress: string | null;
    provider: ethers.BrowserProvider | null;
}

export default function Sidebar({ sessions, activeSessionId, onNewChat, onSelectSession, userAddress, provider }: SidebarProps) {
    const { isOpen, onOpen, onClose } = useDisclosure();
    const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
    const cancelRef = React.useRef<HTMLButtonElement>(null);
    const { refreshSessions } = useApp();
    const toast = useToast();

    const textColor = useColorModeValue('gray.800', 'gray.200');
    const hoverBgColor = useColorModeValue('gray.100', 'gray.700');
    const activeBgColor = useColorModeValue('blue.50', 'blue.900');

    // Responsive values
    const buttonSize = useBreakpointValue({ base: 'xs', md: 'sm' });
    const textSize = useBreakpointValue({ base: 'xs', md: 'sm' });
    const padding = useBreakpointValue({ base: 2, md: 4 });
    const spacing = useBreakpointValue({ base: 2, md: 4 });
    const iconSize = useBreakpointValue({ base: 'xs', md: 'sm' });

    const handleDeleteClick = (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        setSessionToDelete(sessionId);
        onOpen();
    };

    const handleDeleteConfirm = async () => {
        if (!sessionToDelete || !userAddress || !provider) return;

        try {
            await deleteSession(sessionToDelete, userAddress, provider);
            await refreshSessions();

            if (sessionToDelete === activeSessionId) {
                localStorage.removeItem('activeSessionId');
                onNewChat();
            }

            toast({
                title: "Session deleted",
                status: "success",
                duration: 3000,
                isClosable: true,
            });
        } catch (error) {
            console.error('Error deleting session:', error);
            toast({
                title: "Error",
                description: "Failed to delete session",
                status: "error",
                duration: 3000,
                isClosable: true,
            });
        } finally {
            setSessionToDelete(null);
            onClose();
        }
    };

    return (
        <Box 
            h="100%" 
            p={padding}
            w={{ base: '100%', md: '300px' }}
            position={{ base: 'relative', md: 'fixed' }}
            left={0}
            top={0}
            bottom={0}
        >
            <VStack spacing={spacing} align="stretch" h="100%">
                <Button
                    leftIcon={<FiPlus />}
                    colorScheme="blue"
                    onClick={onNewChat}
                    size={buttonSize}
                    w="100%"
                >
                    New Chat
                </Button>

                <Divider />

                <VStack
                    spacing={spacing}
                    align="stretch"
                    overflowY="auto"
                    flex="1"
                    maxH={{ base: '200px', md: 'calc(100vh - 120px)' }}
                >
                    {sessions.map((session) => (
                        <Button
                            key={session.session_id}
                            variant="ghost"
                            justifyContent="flex-start"
                            bg={session.session_id === activeSessionId ? activeBgColor : 'transparent'}
                            _hover={{ bg: hoverBgColor }}
                            onClick={() => onSelectSession(session.session_id)}
                            size={buttonSize}
                            position="relative"
                            px={2}
                        >
                            <HStack w="100%" justify="space-between" spacing={2}>
                                <Text
                                    isTruncated
                                    color={textColor}
                                    fontSize={textSize}
                                    flex="1"
                                >
                                    {session.messages[0]?.content || 'New Chat'}
                                </Text>
                                <Tooltip label="Delete chat">
                                    <IconButton
                                        aria-label="Delete chat"
                                        icon={<FiTrash2 />}
                                        size={iconSize}
                                        variant="ghost"
                                        onClick={(e) => handleDeleteClick(e, session.session_id)}
                                    />
                                </Tooltip>
                            </HStack>
                        </Button>
                    ))}
                </VStack>

                <AlertDialog
                    isOpen={isOpen}
                    leastDestructiveRef={cancelRef}
                    onClose={onClose}
                >
                    <AlertDialogOverlay>
                        <AlertDialogContent>
                            <AlertDialogHeader fontSize={{ base: 'md', md: 'lg' }} fontWeight="bold">
                                Delete Chat Session
                            </AlertDialogHeader>

                            <AlertDialogBody fontSize={{ base: 'sm', md: 'md' }}>
                                Are you sure you want to delete this chat session? This action cannot be undone.
                            </AlertDialogBody>

                            <AlertDialogFooter>
                                <Button ref={cancelRef} onClick={onClose} size={buttonSize}>
                                    Cancel
                                </Button>
                                <Button colorScheme="red" onClick={handleDeleteConfirm} ml={3} size={buttonSize}>
                                    Delete
                                </Button>
                            </AlertDialogFooter>
                        </AlertDialogContent>
                    </AlertDialogOverlay>
                </AlertDialog>
            </VStack>
        </Box>
    );
} 