import { useState, useEffect } from 'react';
import axios from 'axios';

interface VerificationResult {
  is_valid: boolean;
  recovered_address: string;
  expected_address: string;
  match: boolean;
}

interface HashInfo {
  exists: boolean;
  info?: {
    submitter: string;
    timestamp: string;
  };
}

export const useVerification = (verification_hash?: string, signature?: string) => {
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [hashInfo, setHashInfo] = useState<HashInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const verifyMessage = async () => {
      if (!verification_hash || !signature) {
        setVerificationResult(null);
        setHashInfo(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        // Verify signature
        const verifyResponse = await axios.post<VerificationResult>('http://localhost:8000/verify', {
          verification_hash,
          signature
        });

        setVerificationResult(verifyResponse.data);

        // Check if hash exists on-chain
        const hashResponse = await axios.get<HashInfo>(`http://localhost:8000/verify/hash/${verification_hash}`);
        setHashInfo(hashResponse.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Verification failed');
        setVerificationResult(null);
        setHashInfo(null);
      } finally {
        setLoading(false);
      }
    };

    verifyMessage();
  }, [verification_hash, signature]);

  return {
    verificationResult,
    hashInfo,
    loading,
    error
  };
}; 