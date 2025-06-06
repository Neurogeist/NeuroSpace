import { WagmiProvider } from 'wagmi';
import { base, baseSepolia } from 'wagmi/chains';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createWeb3Modal, useWeb3Modal } from '@web3modal/wagmi/react';
import { useAccount } from 'wagmi';
import { createConfig, http } from 'wagmi';

// ENV vars
const projectId = import.meta.env.VITE_WALLET_CONNECT_PROJECT_ID;
const ENVIRONMENT = import.meta.env.VITE_ENVIRONMENT || 'development';

// Chain setup
let chains: readonly [typeof base] | readonly [typeof baseSepolia];
if (ENVIRONMENT === 'development') {
  chains = [baseSepolia] as const;
} else {
  chains = [base] as const;
}

console.log('Project ID:', projectId);

// Wagmi config
const wagmiConfig = createConfig({
  chains,
  transports: {
    [baseSepolia.id]: http(),
    [base.id]: http(),
  },
});

// Create modal
createWeb3Modal({
  wagmiConfig,
  projectId,
  defaultChain: ENVIRONMENT === 'development' ? baseSepolia : base,
});

const queryClient = new QueryClient();

// Custom Wallet Button
function WalletButton() {
  const { open } = useWeb3Modal();
  const { address, isConnected } = useAccount();

  return (
    <div style={{ marginTop: '20px' }}>
      <button
        onClick={() => open()}
        style={{
          padding: '10px 20px',
          fontSize: '16px',
          borderRadius: '8px',
          backgroundColor: '#333',
          color: 'white',
          cursor: 'pointer',
          border: 'none'
        }}
      >
        {isConnected ? 'Connected' : 'Connect Wallet'}
      </button>
      <div style={{ marginTop: '10px' }}>
        <strong>Address:</strong> {isConnected ? address : 'N/A'}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={queryClient}>
        <div style={{ padding: '40px', fontFamily: 'sans-serif' }}>
          <h1>🧪 NeuroSpace Wallet Demo</h1>
          <WalletButton />
        </div>
      </QueryClientProvider>
    </WagmiProvider>
  );
}
