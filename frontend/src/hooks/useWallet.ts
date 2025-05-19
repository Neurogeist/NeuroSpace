import { useState, useEffect, useCallback } from 'react';
import { ethers } from 'ethers';

interface WalletState {
    address: string | null;
    isConnected: boolean;
    chainId: string | null;
    provider: ethers.BrowserProvider | null;
}

const standardizeAddress = (address: string | null): string | null => {
    return address ? address.toLowerCase() : null;
};

export const useWallet = () => {
    const [walletState, setWalletState] = useState<WalletState>({
        address: null,
        isConnected: false,
        chainId: null,
        provider: null,
    });

    const connect = useCallback(async () => {
        if (typeof window.ethereum === 'undefined') {
            console.error('MetaMask is not installed');
            return;
        }

        try {
            const provider = new ethers.BrowserProvider(window.ethereum);
            const accounts = await provider.send('eth_requestAccounts', []);
            const network = await provider.getNetwork();
            
            setWalletState({
                address: standardizeAddress(accounts[0]),
                isConnected: true,
                chainId: network.chainId.toString(),
                provider,
            });
        } catch (error) {
            console.error('Error connecting wallet:', error);
        }
    }, []);

    const disconnectWallet = useCallback(() => {
        setWalletState({
            address: null,
            isConnected: false,
            chainId: null,
            provider: null,
        });
    }, []);

    useEffect(() => {
        const ethereum = window.ethereum;
        if (!ethereum) return;

        const handleAccountsChanged = (accounts: string[]) => {
            if (accounts.length === 0) {
                disconnectWallet();
            } else {
                setWalletState(prev => ({
                    ...prev,
                    address: standardizeAddress(accounts[0]),
                    isConnected: true,
                }));
            }
        };

        const handleChainChanged = (chainId: string) => {
            setWalletState(prev => ({
                ...prev,
                chainId,
            }));
        };

        ethereum.on('accountsChanged', handleAccountsChanged);
        ethereum.on('chainChanged', handleChainChanged);

        // Check if already connected
        const checkConnection = async () => {
            try {
                const provider = new ethers.BrowserProvider(ethereum);
                const accounts = await provider.listAccounts();
                const network = await provider.getNetwork();
                
                if (accounts.length > 0) {
                    setWalletState({
                        address: standardizeAddress(accounts[0].address),
                        isConnected: true,
                        chainId: network.chainId.toString(),
                        provider,
                    });
                }
            } catch (error) {
                console.error('Error checking wallet connection:', error);
            }
        };

        checkConnection();

        return () => {
            ethereum.removeListener('accountsChanged', handleAccountsChanged);
            ethereum.removeListener('chainChanged', handleChainChanged);
        };
    }, [disconnectWallet]);

    return {
        ...walletState,
        connect,
        disconnectWallet,
    };
}; 