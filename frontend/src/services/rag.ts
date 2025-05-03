import axios from 'axios';
import { API_BASE_URL } from './api';

export interface Document {
    id: string;
    name: string;
    ipfsHash: string;
    status: string;
}

export interface Source {
    id: string;
    snippet: string;
    ipfsHash: string;
    transactionHash: string;
}

export interface RAGResponse {
    response: string;
    sources: Source[];
    verification_hash: string;
    signature: string;
    transaction_hash: string;
    ipfs_cid: string;
}

export const uploadDocument = async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post<Document>(`${API_BASE_URL}/rag/upload`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });

    return response.data;
};

export const queryDocuments = async (query: string): Promise<RAGResponse> => {
    const response = await axios.post<RAGResponse>(`${API_BASE_URL}/rag/query`, {
        query,
    });

    return response.data;
};

export const getDocuments = async (): Promise<Document[]> => {
    const response = await axios.get<Document[]>(`${API_BASE_URL}/rag/documents`);
    return response.data;
};

export const verifyRAGResponse = async (
    verification_hash: string,
    signature: string
): Promise<boolean> => {
    try {
        const response = await axios.post(`${API_BASE_URL}/verify/rag`, {
            verification_hash,
            signature,
        });
        return response.data.verified;
    } catch (error) {
        console.error('Error verifying RAG response:', error);
        return false;
    }
}; 