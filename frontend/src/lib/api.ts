const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    // Default headers
    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };

    const response = await fetch(url, {
        ...options,
        headers,
        credentials: 'include' // Crucial for cross-origin session cookies
    });

    if (response.status === 401 && typeof window !== 'undefined') {
        window.location.href = 'http://localhost:8000/login/';
    }

    if (!response.ok) {
        const errorText = await response.text();
        console.error(`fetchApi Error Body: ${errorText.substring(0, 200)}`);
        let errorMessage = errorText || response.statusText;
        try {
            const errObj = JSON.parse(errorText);
            if (errObj.error) errorMessage = errObj.error;
        } catch {
            // Ignore parse errors for raw text responses
        }
        throw new Error(errorMessage);
    }

    const text = await response.text();
    try {
        return JSON.parse(text);
    } catch (err) {
        console.error(`fetchApi Parse Error. Body prefix: ${text.substring(0, 100)}`);
        throw err;
    }
}
