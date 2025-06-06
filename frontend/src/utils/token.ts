export interface TokenPayload {
    sub: string;
    exp: number;
    iat: number;
}

export const decodeToken = (token: string): TokenPayload | null => {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch {
        return null;
    }
};

export const isTokenExpired = (token: string): boolean => {
    const payload = decodeToken(token);
    if (!payload) return true;
    
    const expirationTime = new Date(payload.exp * 1000);
    return expirationTime <= new Date();
};

export const isTokenExpiringSoon = (token: string, minutes = 5): boolean => {
    const payload = decodeToken(token);
    if (!payload) return true;
    
    const expirationTime = new Date(payload.exp * 1000);
    const now = new Date();
    const timeUntilExpiration = expirationTime.getTime() - now.getTime();
    return timeUntilExpiration <= minutes * 60 * 1000;
};

export const getTokenExpirationTime = (token: string): Date | null => {
    const payload = decodeToken(token);
    if (!payload) return null;
    
    return new Date(payload.exp * 1000);
};

export const getTokenWalletAddress = (token: string): string | null => {
    const payload = decodeToken(token);
    if (!payload) return null;
    
    return payload.sub;
}; 