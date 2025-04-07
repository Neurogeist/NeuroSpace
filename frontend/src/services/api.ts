import axios from 'axios';

export const API_BASE_URL = 'http://localhost:8000';

// Configure axios defaults
axios.defaults.withCredentials = false;
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.headers.common['X-User-Address'] = '0x1234567890123456789012345678901234567890'; // Temporary placeholder

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
  ipfs_cid: string;
  transaction_hash: string;
  session_id: string;
  metadata: {
    temperature: number;
    max_tokens: number;
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
  ipfsHash?: string;
  transactionHash?: string;
  metadata?: {
    model: string;
    model_id: string;
    temperature: number;
    max_tokens: number;
  };
}

export const getAvailableModels = async (): Promise<Model[]> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/models`);
    const models = response.data.models;
    return Object.entries(models).map(([name, id]) => ({
      name,
      description: id as string
    }));
  } catch (error) {
    console.error('Error fetching models:', error);
    return [];
  }
};

export const submitPrompt = async (
  prompt: string,
  modelName: string,
  sessionId?: string
): Promise<PromptResponse> => {
  try {
    console.log('Submitting prompt:', { prompt, modelName, sessionId });
    
    // Create specific request config
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'X-User-Address': '0x1234567890123456789012345678901234567890'
      },
      withCredentials: false
    };
    
    const data = {
      prompt,
      model_name: modelName,
      session_id: sessionId
    };
    
    console.log('Request config:', config);
    console.log('Request data:', data);
    
    const response = await axios.post(`${API_BASE_URL}/prompt`, data, config);
    console.log('Response received:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error submitting prompt:', error);
    if (axios.isAxiosError(error)) {
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error('Response data:', error.response.data);
        console.error('Response status:', error.response.status);
        throw new Error(`Server error: ${error.response.status} - ${error.response.data?.detail || error.message}`);
      } else if (error.request) {
        // The request was made but no response was received
        console.error('No response received from server');
        throw new Error('No response received from server. Please check if the API is running.');
      } else {
        // Something happened in setting up the request that triggered an Error
        throw new Error(`Request setup error: ${error.message}`);
      }
    }
    throw error;
  }
};

export const getSessions = async (): Promise<ChatSession[]> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/sessions`);
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