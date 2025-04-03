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

export interface ModelMetadata {
  model: string;
  model_id: string;
  temperature: number;
  max_tokens: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  ipfsHash?: string;
  transactionHash?: string;
  metadata?: ModelMetadata;
} 