import React from 'react';
import {
    Box,
    VStack,
    Button,
    Text,
    useColorModeValue,
    Divider,
    HStack,
    IconButton,
    Tooltip
} from '@chakra-ui/react';
import { FiPlus, FiTrash2 } from 'react-icons/fi';
import { ChatSession } from '../types/chat';

interface SidebarProps {
    sessions: ChatSession[];
    activeSessionId: string | null;
    onNewChat: () => void;
    onSelectSession: (sessionId: string) => void;
}

export default function Sidebar({ sessions, activeSessionId, onNewChat, onSelectSession }: SidebarProps) {
    const bgColor = useColorModeValue('white', 'gray.800');
    const textColor = useColorModeValue('gray.800', 'gray.200');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const hoverBgColor = useColorModeValue('gray.100', 'gray.700');
    const activeBgColor = useColorModeValue('blue.50', 'blue.900');

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
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            // TODO: Implement delete functionality
                                        }}
                                    />
                                </Tooltip>
                            </HStack>
                        </Button>
                    ))}
                </VStack>
            </VStack>
        </Box>
    );
} 