import axios from 'axios';
import { API_BASE_URL } from './api';
import { getAuthHeaders } from './auth';
import { ethers } from 'ethers';
import { AxiosHeaders } from 'axios';

console.log("API_BASE_URL =", API_BASE_URL);

export interface Agent {
    agent_id: string;
    display_name: string;
    description: string;
    capabilities: string[];
    example_queries: string[];
    is_available: boolean;
}

export interface AgentQueryRequest {
    query: string;
    agent_id: string;
    session_id?: string;
}

export interface AgentQueryResponse {
    answer: string;
    trace_id: string;
    ipfs_hash: string;
    commitment_hash: string;
    metadata: {
        agent_id: string;
        start_time: string;
        end_time: string;
        steps: Array<{
            step_id: string;
            action: string;
            timestamp: string;
            inputs: any;
            outputs: any;
            metadata: any;
            step_hash: string;
        }>;
        commitment_hash: string;
        ipfs_hash: string;
    };
}

export const getAgents = async (
    walletAddress: string,
    provider: ethers.BrowserProvider
): Promise<Agent[]> => {
    console.log("[getAgents] Starting request with API_BASE_URL:", API_BASE_URL);
    
    // Log raw auth headers
    const authHeaders = await getAuthHeaders(walletAddress, provider);
    console.log("[getAgents] Raw auth headers:", authHeaders);
    
    // Log headers after AxiosHeaders conversion
    const headers = new AxiosHeaders(authHeaders as Record<string, string>);
    console.log("[getAgents] Converted headers:", headers);
    
    // Log full request URL
    const requestUrl = `${API_BASE_URL}/agents`;
    console.log("[getAgents] Full request URL:", requestUrl);
    
    // Log request configuration
    const config = {
        headers,
        maxRedirects: 5, // Allow redirects to see if Railway is redirecting
        validateStatus: null // Allow all status codes to see what's happening
    };
    console.log("[getAgents] Request config:", config);
    
    try {
        const response = await axios.get<Agent[]>(requestUrl, config);
        console.log("[getAgents] Response status:", response.status);
        console.log("[getAgents] Response headers:", response.headers);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error)) {
            console.error("[getAgents] Axios error details:", {
                status: error.response?.status,
                statusText: error.response?.statusText,
                headers: error.response?.headers,
                data: error.response?.data,
                config: {
                    url: error.config?.url,
                    method: error.config?.method,
                    headers: error.config?.headers
                }
            });
        }
        throw error;
    }
};

export const queryAgent = async (
    request: AgentQueryRequest,
    walletAddress: string,
    provider: ethers.BrowserProvider
): Promise<AgentQueryResponse> => {
    const authHeaders = await getAuthHeaders(walletAddress, provider);
    const response = await axios.post<AgentQueryResponse>(
        `${API_BASE_URL}/agents/query`,
        request,
        { headers: authHeaders }
    );
    return response.data;
}; 