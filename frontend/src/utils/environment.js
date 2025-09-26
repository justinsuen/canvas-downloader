/**
 * isProduction detects if the application is running in production environment
 */
export const isProduction = () => {
  return process.env.NODE_ENV === 'production' || process.env.REACT_APP_NODE_ENV === 'production';
};

/**
 * getApiConfig gets API configuration based on current environment
 */
export const getApiConfig = () => {
  const production = isProduction();

  // Production: Use full API URL if provided, otherwise construct from parts
  if (production) {
    const fullApiUrl = process.env.REACT_APP_API_URL;
    if (fullApiUrl) {
      return {
        API_BASE: fullApiUrl,
        API_URL: `${fullApiUrl}/api`
      };
    }

    // Fallback to constructing URL with HTTPS
    const apiHost = process.env.REACT_APP_API_HOST || window.location.hostname;
    const apiPort = process.env.REACT_APP_API_PORT || '443';
    const protocol = 'https';
    const API_BASE = apiPort === '443' ? `${protocol}://${apiHost}` : `${protocol}://${apiHost}:${apiPort}`;

    return {
      API_BASE,
      API_URL: `${API_BASE}/api`
    };
  } else {
    // Development: Use localhost with HTTP
    const apiPort = process.env.REACT_APP_API_PORT || 8000;
    const apiHost = process.env.REACT_APP_API_HOST || 'localhost';
    const API_BASE = `http://${apiHost}:${apiPort}`;

    return {
      API_BASE,
      API_URL: `${API_BASE}/api`
    };
  }
};