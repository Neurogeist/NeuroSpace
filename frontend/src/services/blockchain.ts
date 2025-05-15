import { ethers } from 'ethers';
import { MetaMaskInpageProvider } from '@metamask/providers';

declare global {
  interface Window {
    ethereum?: MetaMaskInpageProvider | any;
  }
}

const PAYMENT_CONTRACT_ADDRESS = import.meta.env.VITE_PAYMENT_CONTRACT_ADDRESS;
const NEUROCOIN_PAYMENT_CONTRACT_ADDRESS = import.meta.env.VITE_NEUROCOIN_PAYMENT_CONTRACT_ADDRESS;
const NEUROCOIN_ADDRESS = import.meta.env.VITE_NEUROCOIN_ADDRESS;
const ENVIRONMENT = import.meta.env.VITE_ENVIRONMENT || 'development';

const NETWORK_CONFIG = {
    development: {
        chainId: '0x14a34',
        chainName: 'Base Sepolia',
        rpcUrl: 'https://sepolia.base.org',
        blockExplorerUrl: 'https://sepolia.basescan.org'
    },
    production: {
        chainId: '0x2105',
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

const NEUROCOIN_PAYMENT_ABI = [
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
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "pricePerMessage",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "neuroCoin",
        "outputs": [
            {
                "internalType": "contract IERC20",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "paused",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
];

const NEUROCOIN_TOKEN_ABI = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "spender",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "approve",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "owner",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "spender",
                "type": "address"
            }
        ],
        "name": "allowance",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "account",
                "type": "address"
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
];

export const connectWallet = async (): Promise<string> => {
    if (!window.ethereum) {
        throw new Error('MetaMask is not installed');
    }

    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
    
    const chainId = await window.ethereum.request({ method: 'eth_chainId' });
    if (chainId !== currentNetwork.chainId) {
        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: currentNetwork.chainId }],
            });
        } catch (error: any) {
            if (error.code === 4902) {
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

export const getPaymentContract = async (paymentMethod: 'ETH' | 'NEURO') => {
    if (!window.ethereum) {
        throw new Error('MetaMask is not installed');
    }
    const provider = new ethers.BrowserProvider(window.ethereum);
    const signer = await provider.getSigner();
    const address = paymentMethod === 'ETH' ? PAYMENT_CONTRACT_ADDRESS : NEUROCOIN_PAYMENT_CONTRACT_ADDRESS;
    const abi = paymentMethod === 'ETH' ? PAYMENT_CONTRACT_ABI : NEUROCOIN_PAYMENT_ABI;
    return new ethers.Contract(address, abi, signer);
};

export const getNeuroCoinContract = async () => {
    if (!window.ethereum) {
        throw new Error('MetaMask is not installed');
    }
    const provider = new ethers.BrowserProvider(window.ethereum);
    const signer = await provider.getSigner();
    
    if (!NEUROCOIN_ADDRESS) {
        throw new Error('NeuroCoin address not configured');
    }
    
    return new ethers.Contract(NEUROCOIN_ADDRESS, NEUROCOIN_TOKEN_ABI, signer);
};

export const getTokenBalance = async (userAddress: string): Promise<string> => {
    try {
        const tokenContract = await getNeuroCoinContract();
        const balance = await tokenContract.balanceOf(userAddress);
        return ethers.formatEther(balance);
    } catch (error) {
        console.error('Error getting token balance:', error);
        return '0';
    }
};

export const checkTokenAllowance = async (userAddress: string): Promise<boolean> => {
    try {
        const tokenContract = await getNeuroCoinContract();
        const paymentContract = await getPaymentContract('NEURO');
        const [allowance, price] = await Promise.all([
            tokenContract.allowance(userAddress, NEUROCOIN_PAYMENT_CONTRACT_ADDRESS),
            paymentContract.pricePerMessage()
        ]);
        return allowance >= price;
    } catch (error) {
        console.error('Error checking token allowance:', error);
        return false;
    }
};

export const approveToken = async () => {
    try {
        const tokenContract = await getNeuroCoinContract();
        const paymentContract = await getPaymentContract('NEURO');
        const price = await paymentContract.pricePerMessage();
        const approvalAmount = price * BigInt(10);
        const tx = await tokenContract.approve(NEUROCOIN_PAYMENT_CONTRACT_ADDRESS, approvalAmount);
        return tx;
    } catch (error) {
        console.error('Error approving tokens:', error);
        throw new Error('Failed to approve tokens');
    }
};

export const getEthBalance = async (userAddress: string): Promise<string> => {
    try {
        const provider = new ethers.BrowserProvider(window.ethereum);
        const balance = await provider.getBalance(userAddress);
        return ethers.formatEther(balance);
    } catch (error) {
        console.error('Error getting ETH balance:', error);
        return '0';
    }
};

export const getRemainingFreeRequests = async (userAddress: string): Promise<number> => {
    try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/free-requests/${userAddress}`);
        if (!response.ok) {
            throw new Error('Failed to fetch free requests');
        }
        const data = await response.json();
        return data.remaining_requests;
    } catch (error) {
        console.error('Error getting free requests:', error);
        return 0;
    }
};

export const payForMessage = async (sessionId: string, paymentMethod: 'ETH' | 'NEURO' | 'FREE' = 'ETH') => {
    if (!window.ethereum) {
        throw new Error('MetaMask is not installed');
    }

    try {
        const userAddress = await window.ethereum.request({ method: 'eth_requestAccounts' });

        if (paymentMethod === 'FREE') {
            // Use free request
            const response = await fetch(`${import.meta.env.VITE_API_URL}/use-free-request`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sessionId,
                    userAddress: userAddress[0]
                })
            });

            if (!response.ok) {
                throw new Error('Failed to use free request');
            }

            // Return a transaction-like object for consistency, but without a hash
            return {
                wait: async () => Promise.resolve(), // Add a no-op wait function
                remainingFreeRequests: (await getRemainingFreeRequests(userAddress[0])) - 1
            };
        }

        // If not using free request, proceed with normal payment
        const contract = await getPaymentContract(paymentMethod);
        
        if (paymentMethod === 'ETH') {
            const balance = await getEthBalance(userAddress[0]);
            const requiredAmount = '0.00001';
            
            if (parseFloat(balance) < parseFloat(requiredAmount)) {
                throw new Error('Insufficient ETH balance. Please bridge ETH to Base using https://bridge.base.org');
            }
            
            return contract.payForMessage(sessionId, {
                value: ethers.parseEther(requiredAmount)
            });
        } else {
            const isApproved = await checkTokenAllowance(userAddress[0]);
            
            if (!isApproved) {
                throw new Error('Token approval required. Please approve tokens first.');
            }

            const isPaused = await contract.paused();
            if (isPaused) {
                throw new Error('Contract is currently paused. Please try again later.');
            }
            
            return contract.payForMessage(sessionId);
        }
    } catch (error) {
        console.error('Error in payForMessage:', error instanceof Error ? error.message : 'Unknown error');
        throw error;
    }
};