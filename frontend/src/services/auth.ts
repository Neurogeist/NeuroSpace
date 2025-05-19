import { ethers } from 'ethers';
import { isTokenExpired, isTokenExpiringSoon } from '../utils/token';

export type AuthHeaders = {
    'Authorization': string;
};

// Add a lock to prevent multiple simultaneous token refreshes
let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

// Cache the auth headers for a short period
let cachedHeaders: { headers: AuthHeaders; timestamp: number } | null = null;
const CACHE_DURATION = 1000; // 1 second cache

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
    // If there's already a refresh in progress, wait for it
    if (isRefreshing && refreshPromise) {
        return refreshPromise;
    }

    isRefreshing = true;
    refreshPromise = (async () => {
        try {
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
        } finally {
            isRefreshing = false;
            refreshPromise = null;
        }
    })();

    return refreshPromise;
};

export const getAuthHeaders = async (
    walletAddress: string,
    provider: ethers.BrowserProvider
): Promise<AuthHeaders> => {
    // Check cache first
    if (cachedHeaders && Date.now() - cachedHeaders.timestamp < CACHE_DURATION) {
        return cachedHeaders.headers;
    }

    let token = localStorage.getItem('jwt_token');
    
    // Check if we need a new token
    if (!token || isTokenExpired(token) || isTokenExpiringSoon(token)) {
        console.log('Token expired or expiring soon, getting new token...');
        token = await login(walletAddress, provider);
        localStorage.setItem('jwt_token', token);
    }
    
    const headers = {
        'Authorization': `Bearer ${token}`
    };

    // Update cache
    cachedHeaders = {
        headers,
        timestamp: Date.now()
    };
    
    return headers;
}; 