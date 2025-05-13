import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { getRemainingFreeRequests, payForMessage, getEthBalance, getTokenBalance, checkTokenAllowance, approveToken } from '../services/blockchain';
import { useWallet } from '../contexts/WalletContext';

interface PaymentModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (txHash: string) => void;
    sessionId: string;
}

const PaymentModal: React.FC<PaymentModalProps> = ({ isOpen, onClose, onSuccess, sessionId }) => {
    const [paymentMethod, setPaymentMethod] = useState<'ETH' | 'NEURO'>('ETH');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [ethBalance, setEthBalance] = useState<string>('0');
    const [tokenBalance, setTokenBalance] = useState<string>('0');
    const [remainingFreeRequests, setRemainingFreeRequests] = useState<number>(0);
    const { address } = useWallet();

    useEffect(() => {
        if (isOpen && address) {
            const checkBalances = async () => {
                try {
                    console.log('Checking balances for address:', address);
                    const [eth, neuro, free] = await Promise.all([
                        getEthBalance(address),
                        getTokenBalance(address),
                        getRemainingFreeRequests(address)
                    ]);
                    console.log('Free requests:', free);
                    setEthBalance(eth);
                    setTokenBalance(neuro);
                    setRemainingFreeRequests(free);
                } catch (error) {
                    console.error('Error checking balances:', error);
                }
            };
            checkBalances();
        }
    }, [isOpen, address]);

    const handlePayment = async () => {
        if (!address) return;
        
        setIsLoading(true);
        setError(null);

        try {
            console.log('Current free requests:', remainingFreeRequests);
            if (remainingFreeRequests > 0) {
                console.log('Using free request');
                const result = await payForMessage(sessionId, paymentMethod);
                if ('remainingFreeRequests' in result) {
                    console.log('Updated free requests:', result.remainingFreeRequests);
                    setRemainingFreeRequests(result.remainingFreeRequests);
                }
                onSuccess('free-request');
                onClose();
                return;
            }

            if (paymentMethod === 'NEURO') {
                const isApproved = await checkTokenAllowance(address);
                if (!isApproved) {
                    const tx = await approveToken();
                    await tx.wait();
                }
            }

            const tx = await payForMessage(sessionId, paymentMethod);
            onSuccess(typeof tx === 'string' ? tx : tx.hash);
            onClose();
        } catch (error: any) {
            console.error('Payment error:', error);
            setError(error.message || 'Payment failed');
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    const buttonText = isLoading 
        ? 'Processing...' 
        : remainingFreeRequests > 0 
            ? `Use Free Request (${remainingFreeRequests} left)` 
            : 'Pay Now';

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-96">
                <h2 className="text-2xl font-bold mb-4">Payment Required</h2>
                
                {remainingFreeRequests > 0 && (
                    <div className="mb-4 p-3 bg-green-100 rounded-lg">
                        <p className="text-green-800">
                            You have {remainingFreeRequests} free request{remainingFreeRequests !== 1 ? 's' : ''} remaining
                        </p>
                    </div>
                )}

                <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Payment Method
                    </label>
                    <div className="flex space-x-4">
                        <button
                            className={`flex-1 py-2 px-4 rounded-lg ${
                                paymentMethod === 'ETH'
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-gray-200 text-gray-700'
                            }`}
                            onClick={() => setPaymentMethod('ETH')}
                        >
                            Pay with ETH
                            <div className="text-sm">Balance: {parseFloat(ethBalance).toFixed(6)} ETH</div>
                        </button>
                        <button
                            className={`flex-1 py-2 px-4 rounded-lg ${
                                paymentMethod === 'NEURO'
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-gray-200 text-gray-700'
                            }`}
                            onClick={() => setPaymentMethod('NEURO')}
                        >
                            Pay with NeuroCoin
                            <div className="text-sm">Balance: {parseFloat(tokenBalance).toFixed(2)} NEURO</div>
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-100 rounded-lg">
                        <p className="text-red-800">{error}</p>
                    </div>
                )}

                <div className="flex justify-end space-x-4">
                    <button
                        className="px-4 py-2 text-gray-600 hover:text-gray-800"
                        onClick={onClose}
                        disabled={isLoading}
                    >
                        Cancel
                    </button>
                    <button
                        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
                        onClick={handlePayment}
                        disabled={isLoading}
                    >
                        {buttonText}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PaymentModal; 