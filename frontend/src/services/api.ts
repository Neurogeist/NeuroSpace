import axios from 'axios';

const API_URL = 'http://localhost:8000';

interface PromptResponse {
  response: string;
  ipfs_cid: string;
  signature: string;
}

export const submitPrompt = async (prompt: string): Promise<PromptResponse> => {
  try {
    const response = await axios.post(
      `${API_URL}/prompts`,
      {
        prompt,
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