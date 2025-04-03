export interface Message {
    id: string;
    content: string;
    role: 'user' | 'assistant';
    timestamp: string;
    ipfsHash?: string;
    transactionHash?: string;
}

export interface ChatState {
    messages: Message[];
    isLoading: boolean;
    error: string | null;
} 