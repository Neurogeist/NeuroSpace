import axios from 'axios';

const API_URL = 'http://localhost:8000';

export interface Model {
  name: string;
  id: string;
}

export interface PromptResponse {
  response: string;
  ipfs_cid: string;
  signature: string;
  metadata: {
    timestamp: string;
    model_name: string;
    model_id: string;
    temperature: number;
    max_tokens: number;
  };
  model_name: string;
  model_id: string;
}

export const getAvailableModels = async (): Promise<Model[]> => {
  try {
    const response = await axios.get(`${API_URL}/models`);
    const models = response.data.models;
    return Object.entries(models).map(([name, id]) => ({ name, id: id as string }));
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to get models');
    }
    throw error;
  }
};

export const submitPrompt = async (prompt: string, modelName?: string): Promise<PromptResponse> => {
  try {
    const response = await axios.post(
      `${API_URL}/prompts`,
      {
        prompt,
        model_name: modelName,
        timestamp: new Date().toISOString(),
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'X-User-Address': '0x1234567890123456789012345678901234567890',
        },
        withCredentials: false,
      }
    );
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to send message');
    }
    throw error;
  }
}; 