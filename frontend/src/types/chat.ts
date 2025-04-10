export interface ChatMessageMetadata {
    model?: string;
    model_id?: string;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    do_sample?: boolean;
    verification_hash?: string;
    signature?: string;
    ipfs_cid?: string;
    transaction_hash?: string;
    signer_address?: string;
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    metadata?: ChatMessageMetadata;
    verification_hash?: string;
    signature?: string;
    ipfsHash?: string;
    transactionHash?: string;
}

export interface PromptResponse {
    response: string;
    model_name: string;
    model_id: string;
    ipfsHash: string;
    transactionHash: string;
    session_id: string;
    metadata: {
        temperature: number;
        max_tokens: number;
        top_p: number;
        do_sample: boolean;
        num_beams: number;
        early_stopping: boolean;
        verification_hash: string;
        signature: string;
        ipfs_cid: string;
        transaction_hash: string;
    };
}

export interface ChatSession {
    session_id: string;
    messages: ChatMessage[];
    created_at: string;
    updated_at: string;
} 