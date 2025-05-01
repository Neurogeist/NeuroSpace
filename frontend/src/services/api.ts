import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL;
console.log('Loaded API_BASE_URL:', API_BASE_URL);

// Configure axios defaults
axios.defaults.withCredentials = false;
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.headers.common['X-User-Address'] = '0x1234567890123456789012345678901234567890';

// Add response interceptor for better error handling
axios.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error);
    if (error.response) {
      console.error('Response data:', error.response.data);
    }
    return Promise.reject(error);
  }
);

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

export const getAvailableModels = async (): Promise<{ [key: string]: string }> => {
  const response = await axios.get(`${API_BASE_URL}/models`);
  // The backend returns { models: { [name: string]: id } }
  return response.data.models;
};

export const submitPrompt = async (
    prompt: string,
    model: string,
    userAddress: string,
    sessionId?: string,
    txHash?: string   // <-- NEW optional argument
): Promise<PromptResponse> => {
    try {
        const requestBody: any = {
            prompt,
            model,
            user_address: userAddress,
            session_id: sessionId
        };

        if (txHash) {
            requestBody.tx_hash = txHash;   // <-- attach only if exists
        }

        const response = await axios.post(`${API_BASE_URL}/submit_prompt`, requestBody);
        console.log('Prompt response:', response.data);
        return response.data;
    } catch (error) {
        console.error('Error submitting prompt:', error);
        throw error;
    }
};


export const getSessions = async (userAddress: string): Promise<ChatSession[]> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/sessions`, {
      params: {
        wallet_address: userAddress
      }
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 404) {
        // Return empty array if sessions endpoint is not available
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

export const getSession = async (sessionId: string): Promise<ChatSession> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 404) {
        // Return empty session if not found
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
    // Return empty session on any error
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

export async function deleteSession(sessionId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        throw new Error('Failed to delete session');
    }
}

export interface CreateSessionResponse {
  session_id: string;
  created_at: string;
  updated_at: string;
}

export const createSession = async (walletAddress: string): Promise<CreateSessionResponse> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/sessions/create`, {
      wallet_address: walletAddress
    });
    return response.data;
  } catch (error) {
    console.error('Error creating session:', error);
    throw error;
  }
};
