import { isProduction } from './environment';

/**
 * sanitizeMessage removes sensitive data like API keys from log messages
 */
export const sanitizeMessage = (str) => {
  if (typeof str !== 'string') return str;
  return str.replace(/[a-f0-9]{40,}/gi, '[API_KEY_REDACTED]');
};

/**
 * logger provides environment-aware console logging with different levels
 */
export const logger = {
  /**
   * info logs informational messages (dev only)
   */
  info: (message) => {
    if (!isProduction()) {
      console.log(`[INFO] ${sanitizeMessage(message)}`);
    }
  },

  /**
   * warn logs warning messages (all environments)
   */
  warn: (message) => {
    console.warn(`[WARN] ${sanitizeMessage(message)}`);
  },

  /**
   * error logs error messages (all environments)
   */
  error: (message) => {
    console.error(`[ERROR] ${sanitizeMessage(message)}`);
  },

  /**
   * debug logs debug messages with timestamp (dev only)
   */
  debug: (message) => {
    if (!isProduction()) {
      const timestamp = new Date().toLocaleTimeString('en-GB', { hour12: false });
      console.log(`[DEBUG] [${timestamp}] ${sanitizeMessage(message)}`);
    }
  }
};