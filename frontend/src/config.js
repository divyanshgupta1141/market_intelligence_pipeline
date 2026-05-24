let baseUrl = import.meta.env.VITE_API_URL || '';

// Fallback to defaults if no custom URL was provided at build time
if (!baseUrl) {
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    baseUrl = 'http://localhost:8000';
  } else {
    baseUrl = 'https://equisight-api.onrender.com';
  }
}

// Normalize protocol and rewrite Render's private network host to its public URL
if (baseUrl) {
  if (baseUrl === 'equisight-api') {
    baseUrl = 'https://equisight-api.onrender.com';
  } else if (!baseUrl.startsWith('http://') && !baseUrl.startsWith('https://')) {
    baseUrl = `https://${baseUrl}`;
  }
}

export const API_BASE_URL = baseUrl;
