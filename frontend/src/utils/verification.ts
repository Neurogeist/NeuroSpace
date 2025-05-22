// Remove the crypto import
// import { createHash } from 'crypto';

export interface VerificationData {
    prompt: string;
    response: string;
    model_name: string;
    model_id: string;
    temperature: number;
    max_tokens: number;
    system_prompt: string | null;
    timestamp: string;
    wallet_address: string;
    session_id: string;
    rag_sources: any[];  // Empty list for now
    tool_calls: any[];   // Empty list for now
}

function serializeValue(value: any): string {
    if (typeof value === 'number') {
        // Format floats with fixed precision (6 decimal places)
        return value.toFixed(6);
    } else if (typeof value === 'string') {
        return `"${value}"`;
    } else if (value instanceof Date) {
        // Use ISO format without milliseconds and Z
        return value.toISOString().replace(/\.\d{3}Z$/, '');
    } else if (Array.isArray(value)) {
        // Serialize arrays
        const items = value.map(item => serializeValue(item));
        return `[${items.join(',')}]`;
    } else if (typeof value === 'object' && value !== null) {
        return serializeObject(value);
    } else if (value === null) {
        return 'null';
    }
    return String(value);
}

function serializeObject(obj: Record<string, any>): string {
    const sortedKeys = Object.keys(obj).sort();
    const serializedItems = sortedKeys.map(key => {
        const serializedValue = serializeValue(obj[key]);
        return `"${key}":${serializedValue}`; // Remove space after colon
    });
    return `{${serializedItems.join(',')}}`; // Remove space after comma
}

export async function generateVerificationHash(data: VerificationData): Promise<string> {
    // Create a copy of the data to avoid modifying the original
    const dataCopy = { ...data };
    
    // Ensure all required fields are present
    const requiredFields = ['prompt', 'response'];
    
    const missingFields = requiredFields.filter(field => !(field in dataCopy));
    if (missingFields.length > 0) {
        throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
    }
    
    // Format numbers to match backend precision
    if (typeof dataCopy.temperature === 'number') {
        dataCopy.temperature = Number(dataCopy.temperature.toFixed(1));
    }
    if (typeof dataCopy.max_tokens === 'number') {
        dataCopy.max_tokens = Math.round(dataCopy.max_tokens);
    }
    
    // Format rag_sources numbers and sort fields
    if (Array.isArray(dataCopy.rag_sources)) {
        dataCopy.rag_sources = dataCopy.rag_sources.map(source => {
            const formattedSource = {
                ...source,
                chunk_index: Math.round(source.chunk_index),
                // Keep full precision for similarity to match backend
                similarity: source.similarity
            };
            // Sort fields within each source object
            return Object.keys(formattedSource)
                .sort()
                .reduce((obj: Record<string, any>, key) => {
                    obj[key] = formattedSource[key as keyof typeof formattedSource];
                    return obj;
                }, {});
        });
    }
    
    // Sort keys alphabetically to match backend
    const sortedData = Object.keys(dataCopy)
        .sort()
        .reduce((obj: Record<string, any>, key) => {
            obj[key] = dataCopy[key as keyof VerificationData];
            return obj;
        }, {});
    
    // Serialize the data with stable formatting to match backend
    const serializedData = JSON.stringify(sortedData, (key: string, value: any) => {
        // Keep numbers as numbers, don't convert to strings
        if (typeof value === 'number') {
            return value;
        }
        // Format timestamp to match backend (remove milliseconds and Z)
        if (key === 'timestamp' && typeof value === 'string') {
            return value.replace(/\.\d{3}Z?$/, '');
        }
        return value;
    });
    
    console.log('📝 Frontend verification data:', dataCopy);
    console.log('📝 Frontend serialized data:', serializedData);
    
    // Generate SHA-256 hash using Web Crypto API
    const encoder = new TextEncoder();
    const encodedData = encoder.encode(serializedData);
    const hashBuffer = await crypto.subtle.digest('SHA-256', encodedData);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    console.log('🔐 Frontend generated hash:', hashHex);
    return hashHex;
}

export async function verifyHash(verificationData: VerificationData, expectedHash: string): Promise<boolean> {
    try {
        console.log('🔍 Expected hash:', expectedHash);
        const computedHash = await generateVerificationHash(verificationData);
        console.log('🔍 Computed hash:', computedHash);
        console.log('🔍 Hash match:', computedHash === expectedHash);
        return computedHash === expectedHash;
    } catch (error) {
        console.error('Error verifying hash:', error);
        return false;
    }
} 