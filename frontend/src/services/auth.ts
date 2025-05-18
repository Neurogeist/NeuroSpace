import { ethers } from 'ethers';
import { AxiosHeaders } from 'axios';

export type AuthHeaders = {
    'wallet-address': string;
    'wallet-signature': string;
    'wallet-nonce': string;
};

export const generateNonce = (): string => {
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
};

export const signMessage = async (
    walletAddress: string,
    nonce: string,
    provider: ethers.BrowserProvider
): Promise<string> => {
    try {
        const signer = await provider.getSigner();
        const message = `Sign this message to authenticate with NeuroSpace. Nonce: ${nonce}`;
        const signature = await signer.signMessage(message);
        return signature;
    } catch (error) {
        console.error('Error signing message:', error);
        throw error;
    }
};

export const getAuthHeaders = async (
    walletAddress: string,
    provider: ethers.BrowserProvider
): Promise<AuthHeaders> => {
    const nonce = generateNonce();
    const signature = await signMessage(walletAddress, nonce, provider);
    
    return {
        'wallet-address': walletAddress,
        'wallet-signature': signature,
        'wallet-nonce': nonce
    };
}; 