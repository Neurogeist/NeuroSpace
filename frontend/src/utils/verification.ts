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
        return value.toISOString();
    } else if (typeof value === 'object' && value !== null) {
        return serializeObject(value);
    }
    return String(value);
}

function serializeObject(obj: Record<string, any>): string {
    const sortedKeys = Object.keys(obj).sort();
    const serializedItems = sortedKeys.map(key => {
        const serializedValue = serializeValue(obj[key]);
        return `"${key}": ${serializedValue}`;
    });
    return `{${serializedItems.join(', ')}}`;
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
    
    // Serialize the data with stable formatting
    const serializedData = JSON.stringify(dataCopy, Object.keys(dataCopy).sort()).replace(/[\u007f-\uffff]/g, function(chr) {
        return '\\u' + ('0000' + chr.charCodeAt(0).toString(16)).slice(-4);
    });
    

    //console.log('📝 Serialized data (frontend):', serializedData);
    
    // Generate SHA-256 hash using Web Crypto API
    const encoder = new TextEncoder();
    const encodedData = encoder.encode(serializedData);
    const hashBuffer = await crypto.subtle.digest('SHA-256', encodedData);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
}

export async function verifyHash(verificationData: VerificationData, expectedHash: string): Promise<boolean> {
    try {
        const computedHash = await generateVerificationHash(verificationData);
        return computedHash === expectedHash;
    } catch (error) {
        console.error('Error verifying hash:', error);
        return false;
    }
} 