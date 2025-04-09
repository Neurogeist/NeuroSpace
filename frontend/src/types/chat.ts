export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    ipfsHash?: string;
    transactionHash?: string;
    metadata?: {
        model?: string;
        model_id?: string;
        temperature?: number;
        max_tokens?: number;
        top_p?: number;
        do_sample?: boolean;
        num_beams?: number;
        early_stopping?: boolean;
        verification_hash?: string;
        signature?: string;
        ipfs_cid?: string;
        transaction_hash?: string;
    };
}

export interface ChatSession {
    session_id: string;
    messages: ChatMessage[];
    created_at: string;
    updated_at: string;
} 