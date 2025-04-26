import { ethers } from 'ethers';

declare global {
    interface Window {
        ethereum?: any;
    }
}

const PAYMENT_CONTRACT_ADDRESS = import.meta.env.VITE_PAYMENT_CONTRACT_ADDRESS;
const ENVIRONMENT = import.meta.env.VITE_ENVIRONMENT || 'development';

const NETWORK_CONFIG = {
    development: {
        chainId: '0x14a34', // Base Sepolia
        chainName: 'Base Sepolia',
        rpcUrl: 'https://sepolia.base.org',
        blockExplorerUrl: 'https://sepolia.basescan.org'
    },
    production: {
        chainId: '0x2105', // Base Mainnet
        chainName: 'Base',
        rpcUrl: 'https://mainnet.base.org',
        blockExplorerUrl: 'https://basescan.org'
    }
};

const currentNetwork = NETWORK_CONFIG[ENVIRONMENT as keyof typeof NETWORK_CONFIG];

const PAYMENT_CONTRACT_ABI = [
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "sessionId",
                "type": "string"
            }
        ],
        "name": "payForMessage",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
];

export const connectWallet = async (): Promise<string> => {
    if (!window.ethereum) {
        throw new Error('MetaMask is not installed');
    }

    // Request account access
    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
    
    // Check if we're on the correct network
    const chainId = await window.ethereum.request({ method: 'eth_chainId' });
    if (chainId !== currentNetwork.chainId) {
        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: currentNetwork.chainId }],
            });
        } catch (error: any) {
            if (error.code === 4902) {
                // Chain not added to MetaMask
                await window.ethereum.request({
                    method: 'wallet_addEthereumChain',
                    params: [{
                        chainId: currentNetwork.chainId,
                        chainName: currentNetwork.chainName,
                        nativeCurrency: {
                            name: 'ETH',
                            symbol: 'ETH',
                            decimals: 18
                        },
                        rpcUrls: [currentNetwork.rpcUrl],
                        blockExplorerUrls: [currentNetwork.blockExplorerUrl]
                    }],
                });
            }
        }
    }

    return accounts[0];
};

export const getNetworkInfo = () => {
    return {
        name: currentNetwork.chainName,
        explorerUrl: currentNetwork.blockExplorerUrl,
        isProduction: ENVIRONMENT === 'production'
    };
};

export const getPaymentContract = async () => {
    const provider = new ethers.BrowserProvider(window.ethereum);
    const signer = await provider.getSigner();
    return new ethers.Contract(PAYMENT_CONTRACT_ADDRESS, PAYMENT_CONTRACT_ABI, signer);
};

export const payForMessage = async (sessionId: string): Promise<void> => {
    if (!window.ethereum) {
        throw new Error('MetaMask is not installed');
    }

    if (!sessionId || sessionId.length === 0) {
        throw new Error('Session ID is invalid or missing');
    }

    const provider = new ethers.BrowserProvider(window.ethereum);
    const signer = await provider.getSigner();
    const contract = new ethers.Contract(PAYMENT_CONTRACT_ADDRESS!, PAYMENT_CONTRACT_ABI, signer);

    const tx = await contract.payForMessage(sessionId, {
        value: ethers.parseEther('0.00001')
    });

    await tx.wait();
};
