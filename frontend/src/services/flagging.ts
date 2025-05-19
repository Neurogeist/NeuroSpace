import axios from 'axios';
import { API_BASE_URL } from './api';
import { getAuthHeaders } from './auth';
import { ethers } from 'ethers';

export interface FlagMessageRequest {
    message_id: string;
    reason: 'hallucination' | 'inappropriate' | 'inaccurate' | 'other';
    note?: string;
}

export interface FlaggedMessage {
    id: string;
    message_id: string;
    reason: string;
    note?: string;
    wallet_address: string;
    flagged_at: string;
}

export const flagMessage = async (
    messageId: string,
    reason: FlagMessageRequest['reason'],
    note?: string,
    walletAddress?: string,
    provider?: ethers.BrowserProvider
): Promise<FlaggedMessage> => {
    if (!walletAddress || !provider) {
        throw new Error('Wallet address and provider are required for flagging messages');
    }

    try {
        const authHeaders = await getAuthHeaders(walletAddress, provider);
        const response = await axios.post(
            `${API_BASE_URL}/flag`,
            {
                message_id: messageId,
                reason,
                note
            },
            { headers: authHeaders }
        );
        
        return response.data.flagged_message;
    } catch (error) {
        console.error('Error flagging message:', error);
        if (axios.isAxiosError(error)) {
            console.error('Response data:', error.response?.data);
        }
        throw error;
    }
};

export const getFlaggedMessages = async (
    walletAddress?: string,
    reason?: string
): Promise<FlaggedMessage[]> => {
    try {
        const params = new URLSearchParams();
        if (walletAddress) params.append('wallet_address', walletAddress);
        if (reason) params.append('reason', reason);

        const response = await axios.get(
            `${API_BASE_URL}/flagged-messages?${params.toString()}`
        );
        return response.data.flagged_messages;
    } catch (error) {
        console.error('Error getting flagged messages:', error);
        throw error;
    }
}; 