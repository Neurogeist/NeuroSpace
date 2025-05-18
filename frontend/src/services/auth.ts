import { ethers } from 'ethers';
import { AxiosHeaders } from 'axios';

export type AuthHeaders = {
    'Authorization': string;
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
        const message = `Login to NeuroSpace. Nonce: ${nonce}`;
        const signature = await signer.signMessage(message);
        return signature;
    } catch (error) {
        console.error('Error signing message:', error);
        throw error;
    }
};

export const login = async (
    walletAddress: string,
    provider: ethers.BrowserProvider
): Promise<string> => {
    const nonce = generateNonce();
    const signature = await signMessage(walletAddress, nonce, provider);
    
    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            wallet_address: walletAddress,
            signature,
            nonce
        })
    });

    if (!response.ok) {
        throw new Error('Login failed');
    }

    const data = await response.json();
    return data.access_token;
};

export const getAuthHeaders = async (
    walletAddress: string,
    provider: ethers.BrowserProvider
): Promise<AuthHeaders> => {
    // Get token from localStorage or login if not present
    let token = localStorage.getItem('jwt_token');
    
    if (!token) {
        token = await login(walletAddress, provider);
        localStorage.setItem('jwt_token', token);
    }
    
    return {
        'Authorization': `Bearer ${token}`
    };
}; 