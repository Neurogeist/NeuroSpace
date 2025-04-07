import React from 'react';
import {
    Box,
    VStack,
    Button,
    Text,
    IconButton,
    useColorModeValue,
    HStack,
    Divider,
} from '@chakra-ui/react';
import { FiPlus } from 'react-icons/fi';
import { ChatSession } from '../types/chat';

interface SidebarProps {
    sessions: ChatSession[];
    activeSessionId: string | null;
    onNewChat: () => void;
    onSelectSession: (sessionId: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
    sessions,
    activeSessionId,
    onNewChat,
    onSelectSession,
}) => {
    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const hoverBgColor = useColorModeValue('gray.50', 'gray.700');
    const activeBgColor = useColorModeValue('blue.50', 'blue.900');
    const textColor = useColorModeValue('gray.800', 'white');

    const getSessionTitle = (session: ChatSession) => {
        const firstUserMessage = session.messages.find(msg => msg.role === 'user');
        return firstUserMessage?.content || 'New Chat';
    };

    return (
        <Box
            w="250px"
            h="100vh"
            borderRight="1px"
            borderColor={borderColor}
            bg={bgColor}
            p={4}
        >
            <VStack align="stretch" spacing={4}>
                <Button
                    leftIcon={<FiPlus />}
                    colorScheme="blue"
                    variant="outline"
                    onClick={onNewChat}
                >
                    New Chat
                </Button>

                <Divider />

                <VStack align="stretch" spacing={2} overflowY="auto" flex="1">
                    {sessions.map((session) => (
                        <Button
                            key={session.session_id}
                            variant="ghost"
                            justifyContent="flex-start"
                            onClick={() => onSelectSession(session.session_id)}
                            bg={session.session_id === activeSessionId ? activeBgColor : 'transparent'}
                            _hover={{ bg: hoverBgColor }}
                            isTruncated
                        >
                            <Text color={textColor} isTruncated>
                                {getSessionTitle(session)}
                            </Text>
                        </Button>
                    ))}
                </VStack>
            </VStack>
        </Box>
    );
}; 