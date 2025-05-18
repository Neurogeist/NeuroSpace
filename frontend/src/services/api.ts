import axios, { AxiosHeaders } from 'axios';
import { ethers } from 'ethers';
import { getAuthHeaders, login, AuthHeaders } from './auth';

export const API_BASE_URL = import.meta.env.VITE_API_URL;

// Configure axios defaults
axios.defaults.withCredentials = false;
axios.defaults.headers.common['Content-Type'] = 'application/json';

export interface Model {
  name: string;
  description: string;
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

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata: {
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
    timestamp?: string;
    original_prompt?: string;
    wallet_address?: string;
    session_id?: string;
    system_prompt?: string | null;
  };
}

export interface VerificationResponse {
    is_valid: boolean;
    recovered_address: string;
    expected_address?: string;
    match: boolean;
}

export const getAvailableModels = async (
    userAddress: string,
    provider?: ethers.BrowserProvider
): Promise<{ [key: string]: string }> => {
    try {
        const authHeaders = provider ? 
            await getAuthHeaders(userAddress, provider) : 
            undefined;

        const headers = authHeaders ? new AxiosHeaders(authHeaders as Record<string, string>) : undefined;

        const response = await axios.get(`${API_BASE_URL}/models`, { headers });
        return response.data.models;
    } catch (error) {
        console.error('Error getting available models:', error);
        throw error;
    }
};

export const submitPrompt = async (
    prompt: string,
    model: string,
    userAddress: string,
    sessionId?: string,
    txHash?: string,
    paymentMethod: 'ETH' | 'NEURO' | 'FREE' = 'ETH',
    provider?: ethers.BrowserProvider
): Promise<PromptResponse> => {
    try {
        const requestBody: any = {
            prompt,
            model,
            user_address: userAddress,
            session_id: sessionId,
            payment_method: paymentMethod
        };

        // Only include tx_hash if it's a valid transaction hash (not a free request)
        if (txHash && txHash !== 'free-request') {
            requestBody.tx_hash = txHash;
        }

        // Get authentication headers if provider is available
        const authHeaders = provider ? 
            await getAuthHeaders(userAddress, provider) : 
            undefined;

        const headers = authHeaders ? new AxiosHeaders(authHeaders as Record<string, string>) : undefined;

        const response = await axios.post(
            `${API_BASE_URL}/submit_prompt`, 
            requestBody,
            { headers }
        );
        return response.data;
    } catch (error) {
        console.error('Error submitting prompt:', error instanceof Error ? error.message : 'Unknown error');
        throw error;
    }
};

export const getSessions = async (
    userAddress: string,
    provider?: ethers.BrowserProvider
): Promise<ChatSession[]> => {
    try {
        if (!provider) {
            throw new Error('Provider is required for authentication');
        }

        const authHeaders = await getAuthHeaders(userAddress, provider);
        const headers = new AxiosHeaders(authHeaders as Record<string, string>);

        const response = await axios.get(`${API_BASE_URL}/sessions`, {
            headers
        });
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error)) {
            if (error.response?.status === 404) {
                console.log('Sessions endpoint not available, returning empty array');
                return [];
            }
            console.error('Error fetching sessions:', error.response?.data);
        } else {
            console.error('Error fetching sessions:', error);
        }
        return [];
    }
};

export const getSession = async (
    sessionId: string,
    userAddress: string,
    provider?: ethers.BrowserProvider
): Promise<ChatSession> => {
    try {
        const authHeaders = provider ? 
            await getAuthHeaders(userAddress, provider) : 
            undefined;

        const headers = authHeaders ? new AxiosHeaders(authHeaders as Record<string, string>) : undefined;

        const response = await axios.get(
            `${API_BASE_URL}/sessions/${sessionId}`,
            { headers }
        );
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error)) {
            if (error.response?.status === 404) {
                console.log(`Session ${sessionId} not found, returning empty session`);
                return {
                    session_id: sessionId,
                    messages: [],
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                };
            }
            console.error('Error fetching session:', error.response?.data);
        } else {
            console.error('Error fetching session:', error);
        }
        return {
            session_id: sessionId,
            messages: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
    }
};

const verifyCache = new Map<string, Promise<VerificationResponse>>();

export const verifyMessage = async (
  verification_hash: string,
  signature: string,
  expected_address?: string,
  source: string = 'default'
): Promise<VerificationResponse> => {
  const cacheKey = `${verification_hash}_${signature}`;

  if (verifyCache.has(cacheKey)) {
    console.log(`[verifyMessage] Returning cached promise from: ${source}`);
    return verifyCache.get(cacheKey)!;
  }

  console.log(`[verifyMessage] Sending request from: ${source}, Hash: ${verification_hash}`);

  const request = axios.post(`${API_BASE_URL}/verify`, {
    verification_hash,
    signature,
    expected_address
  }, {
    headers: {
      'X-Source': source
    }
  }).then(res => res.data);

  verifyCache.set(cacheKey, request);
  return request;
};

export const deleteSession = async (
    sessionId: string,
    userAddress: string,
    provider?: ethers.BrowserProvider
): Promise<void> => {
    if (!provider) {
        throw new Error('Provider is required for authentication');
    }

    const authHeaders = await getAuthHeaders(userAddress, provider);
    const headers = new AxiosHeaders(authHeaders as Record<string, string>);

    const response = await axios.delete(
        `${API_BASE_URL}/sessions/${sessionId}`,
        { headers }
    );

    if (response.status !== 204) {
        throw new Error('Failed to delete session');
    }
};

export interface CreateSessionResponse {
  session_id: string;
  created_at: string;
  updated_at: string;
}

export const createSession = async (
    walletAddress: string,
    provider?: ethers.BrowserProvider
): Promise<CreateSessionResponse> => {
    try {
        const authHeaders = provider ? 
            await getAuthHeaders(walletAddress, provider) : 
            undefined;

        const headers = authHeaders ? new AxiosHeaders(authHeaders as Record<string, string>) : undefined;

        const response = await axios.post(
            `${API_BASE_URL}/sessions/create`,
            { wallet_address: walletAddress },
            { headers }
        );
        return response.data;
    } catch (error) {
        console.error('Error creating session:', error);
        throw error;
    }
};
