interface TokenPayload {
    exp: number;
    sub: string;
    [key: string]: any;
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
    
    const expirationTime = payload.exp * 1000; // Convert to milliseconds
    const currentTime = Date.now();
    return currentTime >= expirationTime;
};

export const isTokenExpiringSoon = (token: string, thresholdMinutes: number = 1): boolean => {
    const payload = decodeToken(token);
    if (!payload) return true;
    
    const expirationTime = payload.exp * 1000;
    const currentTime = Date.now();
    const thresholdMs = thresholdMinutes * 60 * 1000;
    return (expirationTime - currentTime) < thresholdMs;
};

export const getTokenExpirationTime = (token: string): Date | null => {
    const payload = decodeToken(token);
    if (!payload) return null;
    
    return new Date(payload.exp * 1000);
}; 