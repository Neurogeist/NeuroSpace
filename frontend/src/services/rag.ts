import axios from 'axios';
import { API_BASE_URL } from './api';
import { getAuthHeaders } from './auth';
import { ethers } from 'ethers';

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
    chunk_index: number;
    similarity: number;
    transaction_hash?: string;
}

export interface RAGResponse {
    response: string;
    sources: Source[];
    verification_hash: string;
    signature: string;
    transaction_hash: string;
    ipfs_cid: string;
}

export const uploadDocument = async (
    file: File,
    walletAddress: string,
    provider: ethers.BrowserProvider
): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);

    const authHeaders = await getAuthHeaders(walletAddress, provider);
    const headers = {
        ...authHeaders,
        'Content-Type': 'multipart/form-data',
    };

    const response = await axios.post<Document>(`${API_BASE_URL}/rag/upload`, formData, { headers });
    return response.data;
};

export const queryDocuments = async (
    query: string,
    walletAddress: string,
    provider: ethers.BrowserProvider
): Promise<RAGResponse> => {
    const authHeaders = await getAuthHeaders(walletAddress, provider);
    const response = await axios.post<RAGResponse>(
        `${API_BASE_URL}/rag/query`,
        {
            query,
            wallet_address: walletAddress,
        },
        { headers: authHeaders }
    );
    return response.data;
};

export const getDocuments = async (
    walletAddress: string,
    provider: ethers.BrowserProvider
): Promise<Document[]> => {
    const authHeaders = await getAuthHeaders(walletAddress, provider);
    const response = await axios.get<Document[]>(`${API_BASE_URL}/rag/documents`, {
        headers: authHeaders
    });
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

export const deleteDocument = async (
    documentId: string,
    walletAddress: string,
    provider: ethers.BrowserProvider
): Promise<void> => {
    const authHeaders = await getAuthHeaders(walletAddress, provider);
    await axios.delete(`${API_BASE_URL}/rag/documents/${documentId}`, {
        headers: authHeaders
    });
}; 