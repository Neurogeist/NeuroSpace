import axios from 'axios';
import { API_BASE_URL } from './api';
import { getAuthHeaders } from './auth';
import { ethers } from 'ethers';

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
    const authHeaders = await getAuthHeaders(walletAddress, provider);
    const response = await axios.get<Agent[]>(`${API_BASE_URL}/agents`, {
        headers: authHeaders
    });
    return response.data;
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