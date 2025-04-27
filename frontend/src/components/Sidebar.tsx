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
    useToast
} from '@chakra-ui/react';
import { FiPlus, FiTrash2 } from 'react-icons/fi';
import { ChatSession } from '../types/chat';
import { deleteSession } from '../services/api';
import { useApp } from '../context/AppContext';

interface SidebarProps {
    sessions: ChatSession[];
    activeSessionId: string | null;
    onNewChat: () => void;
    onSelectSession: (sessionId: string) => void;
}

export default function Sidebar({ sessions, activeSessionId, onNewChat, onSelectSession }: SidebarProps) {
    const { isOpen, onOpen, onClose } = useDisclosure();
    const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
    const cancelRef = React.useRef<HTMLButtonElement>(null);
    const { refreshSessions } = useApp();
    const toast = useToast();

    const textColor = useColorModeValue('gray.800', 'gray.200');
    const hoverBgColor = useColorModeValue('gray.100', 'gray.700');
    const activeBgColor = useColorModeValue('blue.50', 'blue.900');

    const handleDeleteClick = (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        setSessionToDelete(sessionId);
        onOpen();
    };

    const handleDeleteConfirm = async () => {
        if (!sessionToDelete) return;

        try {
            await deleteSession(sessionToDelete);
            await refreshSessions();

            // If the deleted session was active, clear it
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
        <Box h="100%" p={4}>
            <VStack spacing={4} align="stretch" h="100%">
                <Button
                    leftIcon={<FiPlus />}
                    colorScheme="blue"
                    onClick={onNewChat}
                    size="sm"
                >
                    New Chat
                </Button>

                <Divider />

                <VStack
                    spacing={2}
                    align="stretch"
                    overflowY="auto"
                    flex="1"
                >
                    {sessions.map((session) => (
                        <Button
                            key={session.session_id}
                            variant="ghost"
                            justifyContent="flex-start"
                            bg={session.session_id === activeSessionId ? activeBgColor : 'transparent'}
                            _hover={{ bg: hoverBgColor }}
                            onClick={() => onSelectSession(session.session_id)}
                            size="sm"
                            position="relative"
                        >
                            <HStack w="100%" justify="space-between">
                                <Text
                                    isTruncated
                                    color={textColor}
                                    fontSize="sm"
                                >
                                    {session.messages[0]?.content || 'New Chat'}
                                </Text>
                                <Tooltip label="Delete chat">
                                    <IconButton
                                        aria-label="Delete chat"
                                        icon={<FiTrash2 />}
                                        size="xs"
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
                            <AlertDialogHeader fontSize="lg" fontWeight="bold">
                                Delete Chat Session
                            </AlertDialogHeader>

                            <AlertDialogBody>
                                Are you sure you want to delete this chat session? This action cannot be undone.
                            </AlertDialogBody>

                            <AlertDialogFooter>
                                <Button ref={cancelRef} onClick={onClose}>
                                    Cancel
                                </Button>
                                <Button colorScheme="red" onClick={handleDeleteConfirm} ml={3}>
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