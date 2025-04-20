import { ethers } from 'ethers';

declare global {
    interface Window {
        ethereum?: any;
    }
}

const PAYMENT_CONTRACT_ADDRESS = import.meta.env.VITE_PAYMENT_CONTRACT_ADDRESS;
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
    
    // Check if we're on the correct network (Base Sepolia)
    const chainId = await window.ethereum.request({ method: 'eth_chainId' });
    if (chainId !== '0x14a34') { // Base Sepolia chain ID
        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: '0x14a34' }],
            });
        } catch (error: any) {
            if (error.code === 4902) {
                // Chain not added to MetaMask
                await window.ethereum.request({
                    method: 'wallet_addEthereumChain',
                    params: [{
                        chainId: '0x14a34',
                        chainName: 'Base Sepolia',
                        nativeCurrency: {
                            name: 'ETH',
                            symbol: 'ETH',
                            decimals: 18
                        },
                        rpcUrls: ['https://sepolia.base.org'],
                        blockExplorerUrls: ['https://sepolia.basescan.org']
                    }],
                });
            }
        }
    }

    return accounts[0];
};

export const payForMessage = async (sessionId: string): Promise<void> => {
    if (!window.ethereum) {
        throw new Error('MetaMask is not installed');
    }

    const provider = new ethers.BrowserProvider(window.ethereum);
    const signer = await provider.getSigner();
    const contract = new ethers.Contract(PAYMENT_CONTRACT_ADDRESS!, PAYMENT_CONTRACT_ABI, signer);

    const tx = await contract.payForMessage(sessionId, {
        value: ethers.parseEther('0.00001')
    });

    await tx.wait();
}; 